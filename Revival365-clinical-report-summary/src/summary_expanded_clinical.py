#!/usr/bin/env python3
"""
Usage:
    python parse_thyrocare.py input.xml [output.json]

Parses the given Thyrocare XML report, extracts patient data
and test results, classifies them according to medically accepted
reference ranges, prints a summary, and writes a JSON output.
Includes derived markers (TGL/HDL ratio, etc.) and annotations for
"High"/"Low" along with the applied range.
"""

import sys
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import requests
from io import BytesIO
def safe_text(element):
    """Return stripped text from an XML element or empty string if missing."""
    return element.text.strip() if element is not None and element.text else ""

################################################################
# 1. Helper: Age bracket
################################################################

def get_age_bracket(age: int) -> str:
    """Return '<65' if age < 65 else '>=65'."""
    return "<65" if age < 65 else ">=65"


################################################################
# 2. Special Classification Functions (Medically Accepted)
################################################################

def classify_hscrp(value: float):
    """
    HsCRP (mg/L):
      < 1   => Good (low risk)
      1-3   => Concern (intermediate risk)
      > 3   => Bad (high risk)
    """
    if value < 1:
        return {"classification": "Good", "low_high": None, "range_applied": "<1"}
    elif value <= 3:
        return {"classification": "Concern", "low_high": None, "range_applied": "1-3"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": ">3"}

def classify_cpeptide(value: float):
    """
    C-Peptide (ng/mL):
      <1.10   => Bad (Low)
      1.10-4.40 => Good
      >4.40   => Bad (High)
    """
    if value < 1.10:
        return {"classification": "Bad", "low_high": "Low", "range_applied": "1.10-4.40"}
    elif value <= 4.40:
        return {"classification": "Good", "low_high": None, "range_applied": "1.10-4.40"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": "1.10-4.40"}


def classify_ldl(value: float, age: int, sex: str):
    """
    LDL Cholesterol (mg/dL):
      Optimal if < 100, else Bad.
    """
    if value < 100:
        return {"classification": "Good", "low_high": None, "range_applied": "<100"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": "<100"}

def classify_non_hdl(value: float, age: int):
    """
    Non-HDL Cholesterol (mg/dL):
      Good if < 130, else Bad.
    """
    if value < 160:
        return {"classification": "Good", "low_high": None, "range_applied": "<160"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": "<160"}

def classify_tgl_hdl_ratio(tgl_value: float, hdl_value: float):
    """
    TGL/HDL ratio:
      Optimal if ratio < 2.0, else Bad.
    """
    if hdl_value <= 0:
        return {"classification": "Unknown", "low_high": None, "range_applied": "HDL=0"}
    ratio = tgl_value / hdl_value
    if ratio < 2.0:
        return {"classification": "Good", "low_high": None, "range_applied": "<2"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": "<2"}

def classify_nlr(neut_value: float, lymph_value: float):
    """
    NLR (Neutrophil / Lymphocyte ratio):
      Normal if 1.0-3.0, else Bad.
    """
    if lymph_value <= 0:
        return {"classification": "Unknown", "low_high": None, "range_applied": "Cannot compute if lymph=0"}
    ratio = neut_value / lymph_value
    if 1.0 <= ratio <= 3.0:
        return {"classification": "Good", "low_high": None, "range_applied": "1.0-3.0"}
    elif ratio < 1.0:
        return {"classification": "Bad", "low_high": "Low", "range_applied": "1.0-3.0"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": "1.0-3.0"}

def classify_homa_ir(insulin_value: float, fbs_value: float):
    """
    HOMA-IR = (insulin * (FBS/18)) / 22.5:
      Considered normal if < 2.0, else Bad.
    """
    if fbs_value <= 0:
        return {"classification": "Unknown", "low_high": None, "range_applied": "FBS must be >0"}
    homa = (insulin_value * (fbs_value / 18.0)) / 22.5
    if homa < 2.0:
        return {"classification": "Good", "low_high": None, "range_applied": "<2"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": "<2"}

def classify_derived_osmolarity(sodium_value: float, bun_value: float, fbs_value: float):
    """
    Calculated Osmolarity = 2*sodium + (BUN/2.8) + (FBS/18):
      Normal if 285-295 mOsm/kg.
    """
    osm = 2 * sodium_value + (bun_value / 2.8) + (fbs_value / 18.0)
    if osm < 285:
        return {"classification": "Bad", "low_high": "Low", "range_applied": "285-295"}
    elif osm > 295:
        return {"classification": "Bad", "low_high": "High", "range_applied": "285-295"}
    else:
        return {"classification": "Good", "low_high": None, "range_applied": "285-295"}


################################################################
# 3. REFERENCE RANGES DICTIONARY (Medically Accepted)
################################################################

REFERENCE_RANGES = {
    # Diabetic Health
    "FASTING_INSULIN": {
        "xml_codes": ["INSFA"],
        "category": "Diabetic_Health",
        "label": "Fasting Insulin (μU/mL)",
        "ctype": "less_than",
        "cutoffs": {"all": 25}
    },
    "FASTING_BLOOD_SUGAR": {
        "xml_codes": ["FBS"],
        "category": "Diabetic_Health",
        "label": "Fasting Blood Sugar (mg/dL)",
        "ctype": "less_than",
        "cutoffs": {"all": 100}
    },
    "HBA1C": {
        "xml_codes": ["HBA"],
        "category": "Diabetic_Health",
        "label": "HbA1c (%)",
        "ctype": "less_than",
        "cutoffs": {"all": 5.7}
    },
    "CPEP": {
        "xml_codes": ["CPEP"],
        "category": "Diabetic_Health",
        "label": "C-Peptide (ng/mL)",
        "ctype": "cpeptide_special",
    },

    # Lipid & Liver
    "TRIG": {
        "xml_codes": ["TRIG"],
        "category": "Lipid_Liver_Profile",
        "label": "Triglycerides (mg/dL)",
        "ctype": "less_than",
        "cutoffs": {"all": 150}
    },
    "HDL": {
        "xml_codes": ["HCHO"],
        "category": "Lipid_Liver_Profile",
        "label": "HDL Cholesterol (mg/dL)",
        "ctype": "hdl_special",  # Sex-specific: M >40, F >50
    },
    "AST": {
        "xml_codes": ["SGOT"],
        "category": "Lipid_Liver_Profile",
        "label": "AST (IU/L)",
        "ctype": "range",
        "cutoffs": {"all": (1, 35)}
    },
    "ALT": {
        "xml_codes": ["SGPT"],
        "category": "Lipid_Liver_Profile",
        "label": "ALT (IU/L)",
        "ctype": "range",
        "cutoffs": {"all": (1, 45)}
    },
    "GGT": {
        "xml_codes": ["GGT"],
        "category": "Lipid_Liver_Profile",
        "label": "GGT (IU/L)",
        "ctype": "ggt_special",  # Sex-specific: M ≤48, F ≤35
    },
    "LDH": {
        "xml_codes": ["LDH"],
        "category": "Lipid_Liver_Profile",
        "label": "LDH (U/L)",
        "ctype": "range",
        "cutoffs": {"all": (120, 250)}
    },

    # Kidney Function
    "EGFR": {
        "xml_codes": ["EGFR"],
        "category": "Kidney_Function",
        "label": "eGFR (mL/min/1.73m²)",
        "ctype": "egfr_special",  # Age-based: <65 => >=90, >=65 => >=60
    },
    "BUN": {
        "xml_codes": ["BUN"],
        "category": "Kidney_Function",
        "label": "BUN (mg/dL)",
        "ctype": "range",
        "cutoffs": {"all": (7, 20)}
    },
    "CREATININE": {
        "xml_codes": ["SCRE"],
        "category": "Kidney_Function",
        "label": "Creatinine (mg/dL)",
        "ctype": "creatinine_special",  # Sex-specific ranges
    },
    "URIC_ACID": {
        "xml_codes": ["URIC"],
        "category": "Kidney_Function",
        "label": "Uric Acid (mg/dL)",
        "ctype": "uric_special",  # Sex-specific cutoffs
    },

    # Cardiac Health
    "HSCRP": {
        "xml_codes": ["HSCRP"],
        "category": "Cardiac_Health",
        "label": "High Sensitivity CRP (mg/L)",
        "ctype": "hscrp_special"
    },
    "LDL": {
        "xml_codes": ["LDL"],
        "category": "Cardiac_Health",
        "label": "LDL Cholesterol (mg/dL)",
        "ctype": "ldl_special"
    },
    "NON_HDL": {
        "xml_codes": ["NHDL"],
        "category": "Cardiac_Health",
        "label": "Non-HDL Cholesterol (mg/dL)",
        "ctype": "nonhdl_special"
    },

    # Inflammatory Markers
    "HOMOCYSTEINE": {
        "xml_codes": ["HOMO"],
        "category": "Inflammatory_Markers",
        "label": "Homocysteine (μmol/L)",
        "ctype": "less_than",
        "cutoffs": {"all": 15}
    },

    # Thyroid Health
    "FT3": {
        "xml_codes": ["FT3"],
        "category": "Thyroid_Health",
        "label": "Free T3 (pg/mL)",
        "ctype": "range",
        "cutoffs": {"all": (2.0, 4.4)}
    },
    "FT4": {
        "xml_codes": ["FT4"],
        "category": "Thyroid_Health",
        "label": "Free T4 (ng/dL)",
        "ctype": "range",
        "cutoffs": {"all": (0.8, 1.8)}
    },
    "TSH": {
        "xml_codes": ["USTSH"],
        "category": "Thyroid_Health",
        "label": "TSH (mIU/L)",
        "ctype": "range",
        "cutoffs": {"all": (0.35, 4.9)}
    },

    # Vitamin & Minerals
    "VITAMIN_D": {
        "xml_codes": ["VITDC"],
        "category": "Vitamin_Minerals",
        "label": "Vitamin D (ng/mL)",
        "ctype":  "range",
        "cutoffs": {"all": (30,100)}
    },
    "VITAMIN_B12": {
        "xml_codes": ["VITB"],
        "category": "Vitamin_Minerals",
        "label": "Vitamin B12 (pg/mL)",
        "ctype":  "range",
        "cutoffs": {"all": (197,771)}
    },
    "SODIUM": {
        "xml_codes": ["SOD"],
        "category": "Vitamin_Minerals",
        "label": "Sodium (mmol/L)",
        "ctype": "range",
        "cutoffs": {"all": (135, 145)}
    },
    "MAGNESIUM": {
        "xml_codes": ["MG"],
        "category": "Vitamin_Minerals",
        "label": "Magnesium (mg/dL)",
        "ctype": "range",
        "cutoffs": {"all": (1.9, 3.2)}
    },
    "PHOSPHOROUS": {
        "xml_codes": ["PHOS"],
        "category": "Vitamin_Minerals",
        "label": "Phosphorous (mg/dL)",
        "ctype": "range",
        "cutoffs": {"all": (2.4, 5.1)}
    },
    "CHLORIDE": {
        "xml_codes": ["CHL"],
        "category": "Vitamin_Minerals",
        "label": "Chloride (mmol/L)",
        "ctype": "range",
        "cutoffs": {"all": (98, 107)}
    },
    "POTASSIUM": {
        "xml_codes": ["POT"],
        "category": "Vitamin_Minerals",
        "label": "Potassium (mmol/L)",
        "ctype": "range",
        "cutoffs": {"all": (3.5, 5.0)}
    },
    "CALCIUM": {
        "xml_codes": ["CALC"],
        "category": "Vitamin_Minerals",
        "label": "Calcium (mg/dL)",
        "ctype": "range",
        "cutoffs": {"all": (8.5, 10.6)}
    },

    # Hormonal Health
    "FREE_TESTOSTERONE": {
        "xml_codes": ["FTES"],
        "category": "Hormonal_Health",
        "label": "Free Testosterone",
        "ctype": "freetestosterone_special",  # Sex-specific ranges
    },
    "ESTROGEN": {
        "xml_codes": ["E2"],
        "category": "Hormonal_Health",
        "label": "Estrogen (Estradiol)",
        "ctype": "estrogen_special",  # Sex-specific ranges
    },
    "IRON": {
        "xml_codes": ["IRON"],
        "category": "Iron_Panel",
        "label": "IRON (μg/dL)",
        "ctype": "range",
        "cutoffs": {"all": (60, 170)}
    },
    "TIBC": {
        "xml_codes": ["TIBC"],
        "category": "Iron_Panel",
        "label": "Total Iron Binding Capacity (μg/dL)",
        "ctype": "range",
        "cutoffs": {"all": (220, 535)}
    },
    "Ferretin": {
        "xml_codes": ["Ferr"],
        "category": "Iron_Panel",
        "label": "Ferritin (ng/mL)",
        "ctype": "ferritin_special",  # Sex-specific ranges
    },
    "TRANSFERRIN_SATURATION": {
        "xml_codes": ["%TSA"],
        "category": "Iron_Panel",
        "label": "Transferrin Saturation (%)",
        "ctype": "range",
        "cutoffs": {"all": (13, 545)}
    },
    "Lipase": {
        "xml_codes": ["LASE"],
        "category": "Liver_Health",
        "label": "Serum Lipase (U/L)",
        "ctype": "range",
        "cutoffs": {"all": (5.6,51.3)}
    },
    "AMYLASE": {
        "xml_codes": ["AMYL"],
        "category": "Liver_Health",
        "label": "Serum Amylase (U/L)",
        "ctype": "range",
        "cutoffs": {"all": (28, 100)}
    },
}


################################################################
# 4. Parsing the XML
################################################################

def parse_patient_info(ptext: str):
    """
    Extracts patient name, age, and sex from strings like:
    'Mr.Vijayarahavan K(40/M)' or 'PALLAVI GULERIA(30Y/F)'
    """
    match = re.match(r"([\w\s\.\-]+)\((\d+)[Yy]?[\/\-](M|F)\)", ptext)
    if match:
        name = match.group(1).strip()
        age = int(match.group(2))
        sex = match.group(3)
        return name, age, sex
    else:
        # fallback if format is unusual
        name = ptext.split("(")[0].strip()
        return name, 0, None


def parse_thyrocare_xml(xml_url: str):
    """
    Reads a Thyrocare XML report and returns a clean structured dictionary
    with patient info and all numeric test results.
    """
    # --- Load XML from URL or local path ---
    if xml_url.lower().startswith("http"):
        response = requests.get(xml_url)
        response.raise_for_status()
        xml_data = BytesIO(response.content)
    else:
        with open(xml_url, "rb") as f:
            xml_data = BytesIO(f.read())

    tree = ET.parse(xml_data)
    root = tree.getroot()

    patient_name = None
    patient_age = 0
    patient_sex = None
    report_date = None
    all_tests = {}

    # --- Traverse XML Structure ---
    for lead in root.findall(".//LEADDETAILS"):
        patient_elem = lead.find("PATIENT")
        if patient_elem is not None:
            ptext = safe_text(patient_elem)
            if ptext and not patient_name:
                name, age, sex = parse_patient_info(ptext)
                patient_name = name
                patient_age = age
                patient_sex = sex

        rrt_elem = lead.find("RRT")
        report_date = safe_text(rrt_elem)

        for test_detail in lead.findall(".//TESTDETAIL"):
            code_elem = test_detail.find("TEST_CODE")
            val_elem = test_detail.find("TEST_VALUE")

            tcode = safe_text(code_elem)
            vtext = safe_text(val_elem)

            if not tcode:
                continue

            # Skip empty or non-numeric test values
            if vtext == "" or vtext.upper() in ("NA", "N/A", "-", "--", "ABSENT", "NORMAL", "NEGATIVE"):
                continue

            # Try to parse numeric values safely
            try:
                vfloat = float(vtext)
                all_tests[tcode] = vfloat
            except ValueError:
                # Some test values may contain text ranges like "10-12"
                num_match = re.findall(r"[-+]?\d*\.?\d+", vtext)
                if num_match:
                    try:
                        all_tests[tcode] = float(num_match[0])
                    except Exception:
                        continue
                else:
                    continue

    return {
        "name": patient_name,
        "age": patient_age,
        "sex": patient_sex,
        "report_date": report_date,
        "tests": all_tests
    }
################################################################
# 5. Classify Single Marker (Updated to Consider Sex)
################################################################

def classification_for_single_value(marker_name, value, age, sex):
    """
    Return a dict:
       {
         "classification": "Good"/"Bad"/"Concern"/"Unknown",
         "low_high": "Low"/"High"/None,
         "range_applied": "some text"
       }
    """
    info = REFERENCE_RANGES[marker_name]
    ctype = info["ctype"]

    if ctype == "hscrp_special":
        return classify_hscrp(value)
    elif ctype == "cpeptide_special":
        return classify_cpeptide(value)
    elif ctype == "ldl_special":
        return classify_ldl(value, age, sex)
    elif ctype == "nonhdl_special":
        return classify_non_hdl(value, age)
    elif ctype == "hdl_special":
        # Sex-specific HDL: M > 40, F > 50; default: >45
        if sex == "M":
            limit = 40
        elif sex == "F":
            limit = 50
        else:
            limit = 45
        range_text = f"> {limit}"
        if value > limit:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
        else:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
    elif ctype == "ggt_special":
        # Sex-specific GGT: M ≤48, F ≤35; default: ≤40
        if sex == "M":
            limit = 48
        elif sex == "F":
            limit = 35
        else:
            limit = 40
        range_text = f"≤ {limit}"
        if value <= limit:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
    elif ctype == "egfr_special":
        # eGFR: <65 => normal if >=90, >=65 => normal if >=60.
        limit = 90 if age < 65 else 60
        range_text = f">= {limit}"
        if value >= limit:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
        else:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
    elif ctype == "creatinine_special":
        # Sex-specific creatinine ranges.
        if sex == "M":
            rng = (0.7, 1.2)
        elif sex == "F":
            rng = (0.5, 1.1)
        else:
            rng = (0.6, 1.2)
        mn, mx = rng
        range_text = f"{mn}-{mx}"
        if value < mn:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
        elif value > mx:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
        else:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
    elif ctype == "uric_special":
        # Sex-specific uric acid cutoffs.
        if sex == "M":
            limit = 7.2
        elif sex == "F":
            limit = 6.0
        else:
            limit = 7.0
        range_text = f"< {limit}"
        if value < limit:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
    elif ctype == "freetestosterone_special":
        # Sex-specific free testosterone.
        if sex == "M":
            rng = (5, 21)
        elif sex == "F":
            rng = (1.46, 2.8)
        else:
            rng = (5, 21)
        mn, mx = rng
        range_text = f"{mn}-{mx}"
        if value < mn:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
        elif value > mx:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
        else:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
    elif ctype == "estrogen_special":
        # Sex-specific estrogen (estradiol).
        if sex == "F":
            rng = (30, 120)
        elif sex == "M":
            rng = (10, 40)
        else:
            rng = (30, 120)
        mn, mx = rng
        range_text = f"{mn}-{mx}"
        if value < mn:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
        elif value > mx:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
        else:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
    elif ctype == "ferritin_special":
        # Sex-specific ferritin.
        if sex == "M":
            rng = (30, 300)
        elif sex == "F":
            rng = (15, 150)
        else:
            rng = (20, 200)
        mn, mx = rng
        range_text = f"{mn}-{mx}"
        if value < mn:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
        elif value > mx:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
        else:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}

    # For standard types ("less_than", "greater_than", "range"):
    bracket = "all"
    cutoffs = info.get("cutoffs", {})

    if ctype == "less_than":
        limit = cutoffs[bracket]
        range_text = f"<{limit}"
        if value < limit:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
    elif ctype == "greater_than":
        limit = cutoffs[bracket]
        range_text = f"> {limit}"
        if value > limit:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
        else:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
    elif ctype == "range":
        rng = cutoffs[bracket]
        mn, mx = rng
        range_text = f"{mn}-{mx}"
        if value < mn:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
        elif value > mx:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
        else:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}

    return {"classification": "Unknown", "low_high": None, "range_applied": "N/A"}


################################################################
# 6. Derived Markers (Medically Accepted)
################################################################

def derive_additional_markers(raw_tests, age, sex):
    """
    Compute derived markers and their classifications.
    """
    derived = {}

    # TGL/HDL Ratio
    if "TRIG" in raw_tests and "HCHO" in raw_tests:
        tgl_val = raw_tests["TRIG"]
        hdl_val = raw_tests["HCHO"]
        result = classify_tgl_hdl_ratio(tgl_val, hdl_val)
        ratio = round(tgl_val / hdl_val, 2) if hdl_val != 0 else None
        derived["TGL_HDL_RATIO"] = {
            "category": "Cardiac_Health",
            "label": "TGL/HDL Ratio",
            "value": ratio,
            "classification": result["classification"],
            "low_high": result["low_high"],
            "range_applied": result["range_applied"]
        }

    # NLR Ratio
    if "ANEU" in raw_tests and "ALYM" in raw_tests:
        neu = raw_tests["ANEU"]
        lym = raw_tests["ALYM"]
        result = classify_nlr(neu, lym)
        ratio = round(neu / lym, 2) if lym != 0 else None
        derived["NLR_RATIO"] = {
            "category": "Cardiac_Health",
            "label": "Neutrophil/Lymphocyte Ratio",
            "value": ratio,
            "classification": result["classification"],
            "low_high": result["low_high"],
            "range_applied": result["range_applied"]
        }

     

     

    return derived


################################################################
# 7. Classify All Tests
################################################################

def classify_all_tests(parsed_data):
    """
    1. Map each test code to its marker.
    2. Classify tests using medically accepted ranges.
    3. Compute derived markers.
    4. Organize results by category.
    """
    name = parsed_data["name"]
    age = parsed_data["age"]
    sex = parsed_data["sex"]
    report_date = parsed_data["report_date"]
    raw_tests = parsed_data["tests"]

    # Map test_code -> marker_name
    code_to_marker = {}
    for mname, info in REFERENCE_RANGES.items():
        for c in info.get("xml_codes", []):
            code_to_marker[c.upper()] = mname

    category_map = defaultdict(list)

    # Classify direct markers
    for tcode, val in raw_tests.items():
        marker_name = code_to_marker.get(tcode.upper())
        if marker_name and isinstance(val, float):
            cresult = classification_for_single_value(marker_name, val, age, sex)
            cat = REFERENCE_RANGES[marker_name]["category"]
            lbl = REFERENCE_RANGES[marker_name]["label"]
            category_map[cat].append({
                "marker_label": lbl,
                "value": val,
                "classification": cresult["classification"],
                "low_high": cresult["low_high"],
                "range_applied": cresult["range_applied"]
            })

    # Derived markers
    derived = derive_additional_markers(raw_tests, age, sex)
    for dkey, dinfo in derived.items():
        cat = dinfo["category"]
        category_map[cat].append({
            "marker_label": dinfo["label"],
            "value": dinfo["value"],
            "classification": dinfo["classification"],
            "low_high": dinfo["low_high"],
            "range_applied": dinfo["range_applied"]
        })

    final_data = {
        "patient_info": {
            "name": name,
            "age": age,
            "sex": sex,
            "report_date": report_date
        },
        "results_by_category": dict(category_map)
    }
    return final_data


################################################################
# 8. Category Roll-up
################################################################

def roll_up_category_tests(tests_list):
    """
    Determine overall category status:
      If any test is "Bad" => overall "Bad";
      Else if any is "Concern" => overall "Concern";
      Else if all are "Good" => overall "Good".
    """
    statuses = [t["classification"] for t in tests_list]
    if any(s == "Bad" for s in statuses):
        return "Bad"
    elif any(s == "Concern" for s in statuses):
        return "Concern"
    elif all(s == "Good" for s in statuses):
        return "Good"
    else:
        return "Unknown"

def roll_up_all_categories(results_by_category):
    cat_status = {}
    for cat, tests in results_by_category.items():
        cat_status[cat] = roll_up_category_tests(tests)
    return cat_status


################################################################
# 9. Output
################################################################

def print_summary(final_data):
    """
    Pretty-print the results, including range information.
    """
    pinfo = final_data["patient_info"]
    name = pinfo["name"]
    age = pinfo["age"]
    sex = pinfo["sex"]
    rdate = pinfo["report_date"]

    print("=" * 60)
    print(f"  Patient Name : {name}")
    print(f"  Age/Sex      : {age} / {sex}")
    print(f"  Report Date  : {rdate}")
    print("=" * 60)

    results_by_category = final_data["results_by_category"]
    cat_status = roll_up_all_categories(results_by_category)

    for cat, tests in results_by_category.items():
        overall = cat_status[cat]
        print(f"\n** {cat} **  (Overall: {overall})")
        for t in tests:
            lbl = t["marker_label"]
            val = t["value"]
            c = t["classification"]
            lh = t["low_high"]
            rng = t["range_applied"]
            if lh:
                print(f"  - {lbl} ({val}) => {c}({lh}), range: {rng}")
            else:
                print(f"  - {lbl} ({val}) => {c}, range: {rng}")
    print()

def write_json_output(final_data, json_file="output.json"):
    """
    Write JSON output with patient info and results.
    """
    results_by_category = final_data["results_by_category"]
    cat_status = roll_up_all_categories(results_by_category)

    output = {
        "patient_info": final_data["patient_info"],
        "results": {}
    }
    for cat, tests in results_by_category.items():
        output["results"][cat] = {
            "category_status": cat_status[cat],
            "tests": tests
        }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"JSON output written to {json_file}")

def create_json_output(final_data):
    """
    Minimal JSON: 
    {
      "patient_info": {...},
      "results": {
         "Diabetic Health": {
            "category_status": "...",
            "tests": [
               {
                 "marker_label": "...",
                 "value": 123.4,
                 "classification": "...",
                 "low_high": "High"/"Low"/None,
                 "range_applied": "<100"
               },
               ...
            ]
         },
         ...
      }
    }
    """
    results_by_category = final_data["results_by_category"]
    cat_status = roll_up_all_categories(results_by_category)

    output = {
        "patient_info": final_data["patient_info"],
        "results": {},
        "summary": {
        "DHA_summary": "dha_summary_data",  # Replace with the actual DHA summary data
        "reviver_summary": "reviver_summary_data"  # Replace with the actual Reviver summary data
    }
    }
    for cat, tests in results_by_category.items():
        output["results"][cat] = {
            "category_status": cat_status[cat],
            "tests": tests
        }
    return output

################################################################
# 10. Main
################################################################

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_thyrocare.py <input.xml> [output.json]")
        sys.exit(1)

    xml_file = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) >= 3 else "output.json"

    # Parse the XML report (expects a URL or file path)
    parsed_data = parse_thyrocare_xml(xml_file)

    # Classify tests using medically accepted ranges
    final_data = classify_all_tests(parsed_data)

    # Print summary
    print_summary(final_data)

    # Write JSON output
    write_json_output(final_data, json_file)


if __name__ == "__main__":
    main()
