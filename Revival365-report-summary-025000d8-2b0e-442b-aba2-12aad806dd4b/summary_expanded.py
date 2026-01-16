#!/usr/bin/env python3
"""
Usage:
    python parse_thyrocare.py input.xml [output.json]

Parses the given Thyrocare XML report, extracts patient data
and test results, classifies them according to the specified
reference ranges (<65 vs. >=65), prints a summary, and writes
a JSON output. Includes derived markers (TGL/HDL ratio, etc.),
and annotations for "High"/"Low" plus displaying the relevant
range/cutoff in both screen output and JSON.
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
# 2. Special Classification Functions
################################################################

def classify_hscrp(value: float):
    """
    HsCRP special classification:
      0-1 => 'Good'
      1-2 => 'Concern'
      3-5 => 'Concern'
      >5  => 'Bad'
    We'll return a dict with:
      classification, low_high, range_applied
    """
    if value < 0:
        return {"classification": "Unknown", "low_high": None, "range_applied": "0-1 optimal, 1-2 low risk, 3-5 moderate, >5 high"}
    if value <= 1:
        return {"classification": "Good", "low_high": None, "range_applied": "0-1 => Good"}
    elif value <= 2:
        return {"classification": "Concern", "low_high": None, "range_applied": "1-2 => Concern (low risk)"}
    elif value <= 5:
        return {"classification": "Concern", "low_high": None, "range_applied": "3-5 => Concern (moderate)"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": ">5 => High risk"}

def classify_cpeptide(value: float):
    """
    C-Peptide logic from your description:
      - <0.5 => "Bad (Low)"
      - 0.5-0.8 => 'Concern' (suboptimal)
      - 0.8-1.4 => 'Good'
      - >1.4 => 'Bad (High)'
    """
    range_text = "0.5-0.8 => Concern, 0.8-1.4 => Good"
    if value < 0.5:
        return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
    elif value < 0.8:
        return {"classification": "Concern", "low_high": None, "range_applied": range_text}
    elif value <= 1.4:
        return {"classification": "Good", "low_high": None, "range_applied": range_text}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": range_text}

def classify_ldl(value: float, age: int):
    """
    Per your note:
      - <65 => LDL <120 => Good
      - >=65 => 80-170 => Good
    else => Bad
    We'll add "High" or "Low" if outside range.
    """
    if age < 65:
        # range_applied = "<120 => Good"
        if value < 120:
            return {"classification": "Good", "low_high": None, "range_applied": "<120"}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": "<120"}
    else:
        # range_applied = "80-170 => Good"
        if 80 <= value <= 170:
            return {"classification": "Good", "low_high": None, "range_applied": "80-170"}
        elif value < 80:
            return {"classification": "Bad", "low_high": "Low", "range_applied": "80-170"}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": "80-170"}

def classify_non_hdl(value: float, age: int):
    """
    Non-HDL:
      - <65 => <140 => Good
      - >=65 => <160 => Good
    We'll annotate "High" if above that, "range_applied" => e.g. "<140".
    """
    if age < 65:
        if value < 140:
            return {"classification": "Good", "low_high": None, "range_applied": "<140"}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": "<140"}
    else:
        if value < 160:
            return {"classification": "Good", "low_high": None, "range_applied": "<160"}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": "<160"}

def classify_tgl_hdl_ratio(tgl_value: float, hdl_value: float, age: int):
    """
    TGL/HDL ratio:
      - <65 => <2 => Good
      - >=65 => <2.5 => Good
    If above that => Bad(High).
    """
    if hdl_value <= 0:
        return {"classification": "Unknown", "low_high": None, "range_applied": "Cannot compute ratio (HDL=0)"}
    ratio = tgl_value / hdl_value
    if age < 65:
        if ratio < 2:
            return {"classification": "Good", "low_high": None, "range_applied": "<2 => Good"}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": "<2 => Good"}
    else:
        if ratio < 2.5:
            return {"classification": "Good", "low_high": None, "range_applied": "<2.5 => Good"}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": "<2.5 => Good"}

def classify_nlr(neut_value: float, lymph_value: float):
    """
    NLR (Neutrophil / Lymphocyte ratio).
    Standard reference ~ 1.0-3.0 => Good
    <1 => "Bad(Low)"? or "Unknown"?
    Let's say <1 => "Bad(Low)", >3 => "Bad(High)".
    """
    if lymph_value <= 0:
        return {"classification": "Unknown", "low_high": None, "range_applied": "1.0-3.0 normal (cannot compute if lymph=0)"}
    ratio = neut_value / lymph_value
    if 1.0 <= ratio <= 3.0:
        return {"classification": "Good", "low_high": None, "range_applied": "1.0-3.0 => Good"}
    elif ratio < 1.0:
        return {"classification": "Bad", "low_high": "Low", "range_applied": "1.0-3.0 => Good"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": "1.0-3.0 => Good"}

def classify_homa_ir(insulin_value: float, fbs_value: float):
    """
    HOMA-IR = (insulin * (fbs/18)) / 22.5
    0.2 - 2.5 => Good
    <0.2 => "Bad(Low)"
    >2.5 => "Bad(High)"
    """
    if fbs_value <= 0:
        return {"classification": "Unknown", "low_high": None, "range_applied": "0.2-2.5 => Good (cannot compute if FBS=0)"}
    homa = (insulin_value * (fbs_value / 18.0)) / 22.5
    if homa < 0.2:
        return {"classification": "Bad", "low_high": "Low", "range_applied": "0.2-2.5 => Good"}
    elif homa <= 2.5:
        return {"classification": "Good", "low_high": None, "range_applied": "0.2-2.5 => Good"}
    else:
        return {"classification": "Bad", "low_high": "High", "range_applied": "0.2-2.5 => Good"}

def classify_derived_osmolarity(sodium_value: float, bun_value: float, fbs_value: float):
    """
    Osmolarity = 2*sodium + (BUN/2.8) + (FBS/18)
    Normal ~ 280-295 => Good
    <280 => Bad(Low), >295 => Bad(High)
    """
    osm = 2*sodium_value + (bun_value/2.8) + (fbs_value/18.0)
    if osm < 280:
        return {"classification": "Bad", "low_high": "Low", "range_applied": "280-295 => Good"}
    elif osm > 295:
        return {"classification": "Bad", "low_high": "High", "range_applied": "280-295 => Good"}
    else:
        return {"classification": "Good", "low_high": None, "range_applied": "280-295 => Good"}


################################################################
# 3. REFERENCE RANGES DICTIONARY
#    For direct markers from the XML
################################################################

REFERENCE_RANGES = {
    # Diabetic Health
    "FASTING_INSULIN": {
        "xml_codes": ["INSFA"],
        "category": "Diabetic_Health",
        "label": "Fasting Insulin",
        "ctype": "less_than",  # standard
        "cutoffs": {
            "<65": 5,
            ">=65": 10
        }
    },
    "FASTING_BLOOD_SUGAR": {
        "xml_codes": ["FBS"],
        "category": "Diabetic_Health",
        "label": "Fasting Blood Sugar",
        "ctype": "less_than",
        "cutoffs": {
            "<65": 100,
            ">=65": 120
        }
    },
    "HBA1C": {
        "xml_codes": ["HBA"],
        "category": "Diabetic_Health",
        "label": "HbA1c",
        "ctype": "less_than",
        "cutoffs": {
            "all": 5.7
        }
    },
    # C-Peptide => custom
    "CPEP": {
        "xml_codes": ["CPEP"],
        "category": "Diabetic_Health",
        "label": "C-Peptide",
        "ctype": "cpeptide_special",
    },

    # Lipid & Liver
    "TRIG": {
        "xml_codes": ["TRIG"],
        "category": "Lipid_Liver_Profile",
        "label": "Triglycerides",
        "ctype": "less_than",
        "cutoffs": {
            "all": 100
        }
    },
    "HDL": {
        "xml_codes": ["HCHO"],
        "category": "Lipid_Liver_Profile",
        "label": "HDL Cholesterol",
        "ctype": "greater_than",
        "cutoffs": {
            "all": 50
        }
    },
    "AST": {
        "xml_codes": ["SGOT"],
        "category": "Lipid_Liver_Profile",
        "label": "AST (SGOT)",
        "ctype": "less_than",
        "cutoffs": {
            "<65": 25,
            ">=65": 30
        }
    },
    "ALT": {
        "xml_codes": ["SGPT"],
        "category": "Lipid_Liver_Profile",
        "label": "ALT (SGPT)",
        "ctype": "less_than",
        "cutoffs": {
            "<65": 25,
            ">=65": 30
        }
    },
    "GGT": {
        "xml_codes": ["GGT"],
        "category": "Lipid_Liver_Profile",
        "label": "GGT",
        "ctype": "less_than",
        "cutoffs": {
            "<65": 25,
            ">=65": 30
        }
    },
    "LDH": {
        "xml_codes": ["LDH"],
        "category": "Lipid_Liver_Profile",
        "label": "LDH",
        "ctype": "range",
        "cutoffs": {
            "<65": (150, 175),
            ">=65": (150, 190)
        }
    },

    # Kidney Function
    "EGFR": {
        "xml_codes": ["EGFR"],
        "category": "Kidney_Function",
        "label": "eGFR",
        "ctype": "greater_than",
        "cutoffs": {
            "<65": 90,
            ">=65": 60
        }
    },
    "BUN": {
        "xml_codes": ["BUN"],
        "category": "Kidney_Function",
        "label": "BUN",
        "ctype": "range",
        "cutoffs": {
            "<65": (12, 22),
            ">=65": (10, 22)
        }
    },
    "CREATININE": {
        "xml_codes": ["SCRE"],
        "category": "Kidney_Function",
        "label": "Creatinine",
        "ctype": "range",
        "cutoffs": {
            "<65": (0.8, 1.1),
            ">=65": (0.8, 1.5)
        }
    },
    "URIC_ACID": {
        "xml_codes": ["URIC"],
        "category": "Kidney_Function",
        "label": "Uric Acid",
        "ctype": "less_than",
        "cutoffs": {
            "all": 5.5
        }
    },

    # Cardiac Health
    "HSCRP": {
        "xml_codes": ["HSCRP"],
        "category": "Cardiac_Health",
        "label": "High Sensitivity CRP",
        "ctype": "hscrp_special"
    },
    "LDL": {
        "xml_codes": ["LDL"],
        "category": "Cardiac_Health",
        "label": "LDL Cholesterol",
        "ctype": "ldl_special"
    },
    "NON_HDL": {
        "xml_codes": ["NHDL"],
        "category": "Cardiac_Health",
        "label": "Non-HDL Cholesterol",
        "ctype": "nonhdl_special"
    },

    # Inflammatory Markers
    "HOMOCYSTEINE": {
        "xml_codes": ["HOMO"],
        "category": "Inflammatory_Markers",
        "label": "Homocysteine",
        "ctype": "less_than",
        "cutoffs": {
            "all": 15
        }
    },

    # Thyroid Health
    "FT3": {
        "xml_codes": ["FT3"],
        "category": "Thyroid_Health",
        "label": "Free T3",
        "ctype": "range",
        "cutoffs": {
            "<65": (3.2, 4.4),
            ">=65": (3.2, 4.8)
        }
    },
    "FT4": {
        "xml_codes": ["FT4"],
        "category": "Thyroid_Health",
        "label": "Free T4",
        "ctype": "range",
        "cutoffs": {
            "all": (1.0, 1.5)
        }
    },
    "TSH": {
        "xml_codes": ["USTSH"],
        "category": "Thyroid_Health",
        "label": "TSH",
        "ctype": "range",
        "cutoffs": {
            "<65": (0.5, 2.8),
            ">=65": (0.5, 3.0)
        }
    },

    # Vitamin & Minerals
    "VITAMIN_D": {
        "xml_codes": ["VITDC"],
        "category": "Vitamin_Minerals",
        "label": "Vitamin D",
        "ctype": "greater_than",
        "cutoffs": {
            "<65": 50,
            ">=65": 40
        }
    },
    "VITAMIN_B12": {
        "xml_codes": ["VITB"],
        "category": "Vitamin_Minerals",
        "label": "Vitamin B12",
        "ctype": "greater_than",
        "cutoffs": {
            "all": 500
        }
    },
    "SODIUM": {
        "xml_codes": ["SOD"],
        "category": "Vitamin_Minerals",
        "label": "Sodium",
        "ctype": "range",
        "cutoffs": {
            "<65": (139, 142),
            ">=65": (139, 147)
        }
    },
    "MAGNESIUM": {
        "xml_codes": ["MG"],
        "category": "Vitamin_Minerals",
        "label": "Magnesium",
        "ctype": "range",
        "cutoffs": {
            "all": (2.0, 2.3)
        }
    },
    "PHOSPHOROUS": {
        "xml_codes": ["PHOS"],
        "category": "Vitamin_Minerals",
        "label": "Phosphorous",
        "ctype": "range",
        "cutoffs": {
            "all": (3.0, 4.0)
        }
    },
    "CHLORIDE": {
        "xml_codes": ["CHL"],
        "category": "Vitamin_Minerals",
        "label": "Chloride",
        "ctype": "range",
        "cutoffs": {
            "<65": (102, 105),
            ">=65": (102, 107)
        }
    },
    "POTASSIUM": {
        "xml_codes": ["POT"],
        "category": "Vitamin_Minerals",
        "label": "Potassium",
        "ctype": "range",
        "cutoffs": {
            "all": (4.0, 4.4)
        }
    },
    "CALCIUM": {
        "xml_codes": ["CALC"],
        "category": "Vitamin_Minerals",
        "label": "Calcium",
        "ctype": "range",
        "cutoffs": {
            "all": (9.4, 9.8)
        }
    },

    # Hormonal Health
    "FREE_TESTOSTERONE": {
        "xml_codes": ["FTES"],
        "category": "Hormonal_Health",
        "label": "Free Testosterone",
        "ctype": "range",
        "cutoffs": {
            "all": (15, 25)
        }
    },
    "ESTROGEN": {
        "xml_codes": ["E2"],
        "category": "Hormonal_Health",
        "label": "Estrogen (Estradiol)",
        "ctype": "range",
        "cutoffs": {
            "all": (20, 30)
        }
    },
    "IRON": {
        "xml_codes": ["IRON"],
        "category": "Iron_Panel",
        "label": "IRON",
        "ctype": "range",
        "cutoffs": {
            "all": (80, 100)
        }
    },
    "TIBC": {
        "xml_codes": ["TIBC"],
        "category": "Iron_Panel",
        "label": "TOTAL IRON BINDING CAPACITY",
        "ctype": "range",
        "cutoffs": {
            "all": (250, 400)
        }
    },
    "Ferretin": {
        "xml_codes": ["Ferr"],
        "category": "Iron_Panel",
        "label": "Ferretin",
        "ctype": "range",
        "cutoffs": {
            "all": (70, 150)
        }
    },
    "TRANSFERRIN_SATURATION": {
        "xml_codes": ["%TSA"],
        "category": "Iron_Panel",
        "label": "TRANSFERRIN SATURATION",
        "ctype": "range",
        "cutoffs": {
            "all": (30, 40)
        }
    },
     "Lipase": {
        "xml_codes": ["LASE"],
        "category": "Liver_Health",
        "label": "Serum Lipase",
        "ctype": "greater_than",
        "cutoffs": {
            "all": 160
        }
    },
    "AMYLASE": {
        "xml_codes": ["AMYL"],
        "category": "Liver_Health",
        "label": "Serum AMYLASE",
        "ctype": "range",
        "cutoffs": {
            "all": (30, 120)
        }
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
# 5. Classify Single Marker
################################################################

def classification_for_single_value(marker_name, value, age):
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

    # Determine correct bracket (if "all" not found, fallback)
    bracket = get_age_bracket(age)
    cutoffs = info.get("cutoffs", {})
    if bracket not in cutoffs and "all" in cutoffs:
        bracket = "all"

    # For "custom" ctype:
    if ctype == "hscrp_special":
        return classify_hscrp(value)
    elif ctype == "cpeptide_special":
        return classify_cpeptide(value)
    elif ctype == "ldl_special":
        return classify_ldl(value, age)
    elif ctype == "nonhdl_special":
        return classify_non_hdl(value, age)

    # Otherwise handle "less_than", "greater_than", or "range"
    if ctype == "less_than":
        limit = cutoffs[bracket]
        # range_applied => f"< {limit}"
        range_text = f"<{limit}"
        if value < limit:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
        else:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}

    elif ctype == "greater_than":
        limit = cutoffs[bracket]
        # range_applied => f"> {limit}"
        range_text = f"> {limit}"
        if value > limit:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}
        else:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}

    elif ctype == "range":
        rng = cutoffs[bracket]  # (min_val, max_val)
        mn, mx = rng
        range_text = f"{mn}-{mx}"
        if value < mn:
            return {"classification": "Bad", "low_high": "Low", "range_applied": range_text}
        elif value > mx:
            return {"classification": "Bad", "low_high": "High", "range_applied": range_text}
        else:
            return {"classification": "Good", "low_high": None, "range_applied": range_text}

    # Fallback
    return {"classification": "Unknown", "low_high": None, "range_applied": "N/A"}


################################################################
# 6. Derived Markers
################################################################

def derive_additional_markers(raw_tests, age):
    """
    Return a dict of derived marker_name => {
      "category": ...,
      "label": ...,
      "value": float or None,
      "classification": "Good"/"Bad"/...,
      "low_high": "Low"/"High"/None,
      "range_applied": ...
    }
    """
    derived = {}

    # TGL/HDL ratio
    if "TRIG" in raw_tests and "HCHO" in raw_tests:
        tgl_val = raw_tests["TRIG"]
        hdl_val = raw_tests["HCHO"]
        result = classify_tgl_hdl_ratio(tgl_val, hdl_val, age)
        ratio = None
        if hdl_val != 0:
            ratio = round(tgl_val / hdl_val, 2)
        derived["TGL_HDL_RATIO"] = {
            "category": "Cardiac_Health",
            "label": "TGL/HDL Ratio",
            "value": ratio,
            "classification": result["classification"],
            "low_high": result["low_high"],
            "range_applied": result["range_applied"]
        }

    # NLR
    if "ANEU" in raw_tests and "ALYM" in raw_tests:
        neu = raw_tests["ANEU"]
        lym = raw_tests["ALYM"]
        result = classify_nlr(neu, lym)
        ratio = round(neu/lym, 2) if lym != 0 else None
        derived["NLR_RATIO"] = {
            "category": "Cardiac_Health",
            "label": "Neutrophil/Lymphocyte Ratio",
            "value": ratio,
            "classification": result["classification"],
            "low_high": result["low_high"],
            "range_applied": result["range_applied"]
        }

    # HOMA-IR
    if "INSFA" in raw_tests and "FBS" in raw_tests:
        ins_val = raw_tests["INSFA"]
        fbs_val = raw_tests["FBS"]
        result = classify_homa_ir(ins_val, fbs_val)
        homa_val = None
        if fbs_val != 0:
            homa_val = (ins_val*(fbs_val/18))/22.5
            homa_val = round(homa_val, 2)
        derived["HOMA_IR"] = {
            "category": "Diabetic_Health",
            "label": "HOMA-IR",
            "value": homa_val,
            "classification": result["classification"],
            "low_high": result["low_high"],
            "range_applied": result["range_applied"]
        }

    # Osmolarity
    if "SOD" in raw_tests and "BUN" in raw_tests and "FBS" in raw_tests:
        sod_val = raw_tests["SOD"]
        bun_val = raw_tests["BUN"]
        glu_val = raw_tests["FBS"]
        result = classify_derived_osmolarity(sod_val, bun_val, glu_val)
        osm_val = round((2*sod_val) + (bun_val/2.8) + (glu_val/18.0), 2)
        derived["OSMOL"] = {
            "category": "Kidney_Function",
            "label": "Osmolarity (calc)",
            "value": osm_val,
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
    1) Match each recognized test_code -> marker
    2) Classify
    3) Create derived markers & classify
    4) Return final structure with categories
    """
    name = parsed_data["name"]
    age = parsed_data["age"]
    sex = parsed_data["sex"]
    report_date = parsed_data["report_date"]
    raw_tests = parsed_data["tests"]

    # Map test_code->marker_name
    code_to_marker = {}
    for mname, info in REFERENCE_RANGES.items():
        for c in info.get("xml_codes", []):
            code_to_marker[c.upper()] = mname

    # We'll store results by category
    category_map = defaultdict(list)

    # Classify direct markers
    for tcode, val in raw_tests.items():
        marker_name = code_to_marker.get(tcode.upper())
        if marker_name and isinstance(val, float):
            # We have a recognized numeric marker
            cresult = classification_for_single_value(marker_name, val, age)
            cat = REFERENCE_RANGES[marker_name]["category"]
            lbl = REFERENCE_RANGES[marker_name]["label"]
            category_map[cat].append({
                "marker_label": lbl,
                "value": val,
                "classification": cresult["classification"],
                "low_high": cresult["low_high"],
                "range_applied": cresult["range_applied"]
            })
        else:
            # unrecognized or non-float => skip or store in 'misc'
            pass

    # Derived markers
    derived = derive_additional_markers(raw_tests, age)
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
    If any test is "Bad", => "Bad"
    Else if any test is "Concern", => "Concern"
    Else => "Good"
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
    Pretty print the results to stdout, including the range text.
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
            # Example line: " - Fasting Blood Sugar (256.51) => Bad(High), range: <100"
            if lh:
                print(f"  - {lbl} ({val}) => {c}({lh}), range: {rng}")
            else:
                print(f"  - {lbl} ({val}) => {c}, range: {rng}")
    print()

def write_json_output(final_data, json_file="output.json"):
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
    if len(sys.argv) >= 3:
        json_file = sys.argv[2]
    else:
        json_file = "output.json"

    # 1) Parse
    parsed_data = parse_thyrocare_xml(xml_file)

    # 2) Classify
    final_data = classify_all_tests(parsed_data)

    # 3) Print summary
    print_summary(final_data)

    # 4) Write JSON
    write_json_output(final_data, json_file)


if __name__ == "__main__":
    main()
