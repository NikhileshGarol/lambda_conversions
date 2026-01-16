import json
import sys
from summary_expanded_clinical import parse_thyrocare_xml
from summary_expanded_clinical import classify_all_tests
from summary_expanded_clinical import create_json_output
import os

def read_lab_report(filename="output.json"):
    """
    Reads the lab report JSON from the specified file
    and returns it as a Python dictionary.
    """
    with open(filename, "r") as f:
        report_json = json.load(f)
    return report_json

# Marker-level explanations depending on classification:
test_explanations = {
    "HbA1c": {
        "Bad": (
            "HbA1c is significantly elevated, indicating poor long-term "
            "blood sugar control and higher risk of diabetic complications."
        ),
        "Good": (
            "HbA1c is within a healthy range, indicating good long-term "
            "blood sugar management."
        )
    },
    "Fasting Blood Sugar": {
        "Bad": (
            "Fasting Blood Sugar is high, suggesting hyperglycemia. "
            "Lifestyle or treatment adjustments may be required."
        ),
        "Good": (
            "Fasting Blood Sugar is normal, suggesting good glucose control "
            "in a fasted state."
        )
    },
    "C-Peptide": {
        "Bad": (
            "C-Peptide is high, which can point to excessive insulin production "
            "or insulin resistance."
        ),
        "Good": (
            "C-Peptide is in normal range, indicating balanced insulin production."
        )
    },
    "Fasting Insulin": {
        "Bad": (
            "Fasting Insulin is elevated, often associated with insulin resistance. "
            "Can lead to metabolic syndrome or diabetes over time."
        ),
        "Good": (
            "Fasting Insulin is within normal limits, suggesting balanced insulin release."
        )
    },
    "HOMA-IR": {
        "Bad": (
            "HOMA-IR is high, indicating substantial insulin resistance, "
            "raising diabetes and cardiovascular risks."
        ),
        "Good": (
            "HOMA-IR is within normal range, indicating healthy insulin sensitivity."
        )
    },
    "Free Testosterone": {
        "Bad": (
            "Free Testosterone is low. This can affect energy, libido, mood, "
            "and muscle mass."
        ),
        "Good": (
            "Free Testosterone is adequate, supporting normal energy and muscle maintenance."
        )
    },
    "Estrogen (Estradiol)": {
        "Bad": (
            "Estradiol is high. In men, elevated estrogen may cause weight gain, "
            "fatigue, or additional hormonal issues."
        ),
        "Good": (
            "Estradiol is within normal limits, supporting balanced hormonal function."
        )
    },
    "Homocysteine": {
        "Bad": (
            "Homocysteine is elevated, which can increase cardiovascular risk "
            "and may indicate vitamin deficiencies."
        ),
        "Good": (
            "Homocysteine is normal, suggesting lower cardiovascular risk from this marker."
        )
    },
    "Vitamin D": {
        "Bad": (
            "Vitamin D is deficient, which can affect bone health, immunity, "
            "and mood. Supplementation or sunlight may help."
        ),
        "Good": (
            "Vitamin D is sufficient, helping to maintain bone density and immune health."
        )
    },
    "Vitamin B12": {
        "Bad": (
            "Vitamin B12 is low, possibly leading to fatigue, neurological issues, "
            "or anemia."
        ),
        "Good": (
            "Vitamin B12 is adequate, supporting healthy red blood cells and nerve function."
        )
    },
    "Magnesium": {
        "Bad": (
            "Magnesium is out of normal range; can affect muscle and nerve function."
        ),
        "Good": (
            "Magnesium is optimal, which is important for muscle, nerve, and enzymatic functions."
        )
    },
    "Phosphorous": {
        "Bad": (
            "Phosphorous is out of normal range; can affect bone health and metabolism."
        ),
        "Good": (
            "Phosphorous is within normal limits, supporting bone and cellular function."
        )
    },
    "Chloride": {
        "Bad": (
            "Chloride is out of normal range; can indicate electrolyte or acid-base imbalances."
        ),
        "Good": (
            "Chloride is in normal range, indicating balanced electrolyte status."
        )
    },
    "Potassium": {
        "Bad": (
            "Potassium is high, which could affect heart rhythm and muscle function."
        ),
        "Good": (
            "Potassium is at a healthy level, vital for heart and muscle function."
        )
    },
    "Sodium": {
        "Bad": (
            "Sodium is out of normal range; can impact fluid balance and blood pressure."
        ),
        "Good": (
            "Sodium is within normal range, supporting fluid balance and nerve function."
        )
    },
    "Calcium": {
        "Bad": (
            "Calcium is slightly low, which may affect bone health and muscle function."
        ),
        "Good": (
            "Calcium is normal, supporting bone strength and muscle contraction."
        )
    },
    "High Sensitivity CRP": {
        "Bad": (
            "hs-CRP is high, indicating inflammation and increased cardiovascular risk."
        ),
        "Good": (
            "hs-CRP is normal, suggesting lower systemic inflammation."
        )
    },
    "LDL Cholesterol": {
        "Bad": (
            "LDL cholesterol is above optimal levels, increasing heart disease risk."
        ),
        "Good": (
            "LDL cholesterol is at a relatively safe level."
        )
    },
    "Non-HDL Cholesterol": {
        "Bad": (
            "Non-HDL cholesterol is high, raising risk for heart disease."
        ),
        "Good": (
            "Non-HDL cholesterol is in a safer range."
        )
    },
    "TGL/HDL Ratio": {
        "Bad": (
            "Triglycerides/HDL ratio is high, suggesting increased cardiovascular risk."
        ),
        "Good": (
            "Triglycerides/HDL ratio is in a good range, indicating healthier lipid balance."
        )
    },
    "Neutrophil/Lymphocyte Ratio": {
        "Bad": (
            "Ratio is off, potentially indicating inflammation or stress."
        ),
        "Good": (
            "Neutrophil/Lymphocyte Ratio is healthy, suggesting balanced immune response."
        )
    },
    "LDH": {
        "Bad": (
            "LDH is elevated, possibly indicating tissue damage or stress."
        ),
        "Good": (
            "LDH is normal, suggesting no major tissue breakdown."
        )
    },
    "GGT": {
        "Bad": (
            "GGT is elevated, indicating possible liver stress or damage."
        ),
        "Good": (
            "GGT is within normal limits, indicating healthy liver function."
        )
    },
    "HDL Cholesterol": {
        "Bad": (
            "HDL is low, reducing protective effects against heart disease."
        ),
        "Good": (
            "HDL is at a healthy level, offering better cardiovascular protection."
        )
    },
    "Triglycerides": {
        "Bad": (
            "Triglycerides are above or borderline, which can increase heart disease risk."
        ),
        "Good": (
            "Triglycerides are within normal range, supporting healthier lipid profiles."
        )
    },
    "AST (SGOT)": {
        "Bad": (
            "AST is high, potentially indicating liver or muscle damage."
        ),
        "Good": (
            "AST is normal, suggesting minimal liver stress or damage."
        )
    },
    "ALT (SGPT)": {
        "Bad": (
            "ALT is high, possibly reflecting liver inflammation or damage."
        ),
        "Good": (
            "ALT is normal, indicating minimal liver stress."
        )
    },
    "Free T3": {
        "Bad": (
            "Free T3 is out of normal range, potentially affecting energy and metabolism."
        ),
        "Good": (
            "Free T3 is within normal limits, supporting healthy metabolism."
        )
    },
    "Free T4": {
        "Bad": (
            "Free T4 is out of normal range; can signal thyroid dysfunction."
        ),
        "Good": (
            "Free T4 is normal, indicating balanced thyroid hormone production."
        )
    },
    "TSH": {
        "Bad": (
            "TSH is high, suggesting potential hypothyroidism which may cause fatigue and weight gain."
        ),
        "Good": (
            "TSH is within normal range, indicating balanced thyroid function."
        )
    },
    "BUN": {
        "Bad": (
            "BUN is out of normal range; can be due to diet, hydration, or kidney function."
        ),
        "Good": (
            "BUN is normal, suggesting typical kidney function and protein metabolism."
        )
    },
    "Creatinine": {
        "Bad": (
            "Creatinine is outside normal range; could indicate muscle mass issues or kidney concerns."
        ),
        "Good": (
            "Creatinine is in normal range, indicating healthy kidney filtration."
        )
    },
    "Uric Acid": {
        "Bad": (
            "Uric Acid is high, possibly leading to gout or kidney problems."
        ),
        "Good": (
            "Uric Acid is within normal limits, reducing risk of gout or kidney stones."
        )
    },
    "eGFR": {
        "Bad": (
            "eGFR is lower than normal, suggesting reduced kidney function."
        ),
        "Good": (
            "eGFR is healthy, indicating good kidney filtration capacity."
        )
    },
    "Osmolarity (calc)": {
        "Bad": (
            "Osmolarity is out of normal range; can indicate fluid/electrolyte imbalance."
        ),
        "Good": (
            "Osmolarity is normal, indicating well-balanced fluid and electrolyte levels."
        )
    }
}

# Category-level base messages, if you want them:
category_base_messages = {
    "Diabetic_Health": (
        "Your diabetic markers reflect blood sugar and insulin levels. "
        "Optimizing these is crucial to prevent complications such as neuropathy, nephropathy, "
        "and cardiovascular risks."
    ),
    "Hormonal_Health": (
        "Hormones impact energy, mood, metabolism, and more. Maintaining a proper balance "
        "improves overall vitality."
    ),
    "Inflammatory_Markers": (
        "Inflammation can be a risk factor for chronic diseases, including heart disease "
        "and autoimmune conditions."
    ),
    "Vitamin_Minerals": (
        "Vitamins and minerals are essential for numerous body functions, including immune support, "
        "bone health, and energy metabolism."
    ),
    "Cardiac_Health": (
        "Cardiac markers help assess your risk for heart disease. High-risk indicators or poor ratios "
        "may require diet, exercise, or medication adjustments."
    ),
    "Lipid_Liver_Profile": (
        "Monitoring liver enzymes and lipid levels is important for cardiovascular health and liver function."
    ),
    "Thyroid_Health": (
        "Thyroid hormones regulate metabolism, energy, and many body systems. "
        "Imbalances can affect weight, mood, and overall health."
    ),
    "Kidney_Function": (
        "Kidneys filter waste and maintain fluid/electrolyte balance. These markers assess kidney performance."
    )
}

def assemble_category_summary(category_name, category_data):
    """
    Creates a concise summary referencing 'Bad' and 'Good' markers in this category.
    Adds a base message for context.
    """
    bad_markers = []
    good_markers = []

    for test in category_data.get("tests", []):
        classification = test.get("classification", "").lower()
        label = test.get("marker_label", "Unknown Marker")
        if classification == "bad":
            bad_markers.append(label)
        elif classification == "good":
            good_markers.append(label)

    category_status = category_data.get("category_status", "").lower()

    base_message = category_base_messages.get(
        category_name, 
        f"Markers in {category_name} are important to overall health."
    )

    # Summaries with icons
    summary = {
    "message": base_message,
    "status": category_status,
    "details": {
        "attention_needed": bad_markers if bad_markers else ["None"],
        "healthy_markers": good_markers if good_markers else ["None"],
        "overall_assessment": (
            "This category shows room for improvement."
            if category_status == "bad"
            else "This category appears to be in good shape."
        ),
    },
}
    return summary


def add_interpretations_and_summaries(report_json):
    """
    - Loops through each category and each test in 'results'.
    - Adds:
        1) A category-level summary (category_summary).
        2) A test-level interpretation text.
    - Returns the updated JSON.
    """
    for category_name, category_data in report_json.get("results", {}).items():
        # Generate a summary for the category
        category_data["category_summary"] = assemble_category_summary(category_name, category_data)

        # Generate interpretation for each marker
        for test in category_data.get("tests", []):
            label = test.get("marker_label")
            classification = test.get("classification", "Good")  # default to Good if missing

            # Assign an interpretation from test_explanations dict
            if label in test_explanations:
                test["interpretation"] = test_explanations[label].get(
                    classification,
                    "No specific interpretation for this classification."
                )
            else:
                test["interpretation"] = "No specific interpretation available for this marker."
    return report_json


def print_colored_report(processed_report):
    """
    Prints the processed report in a user-friendly manner,
    showing icons for Good (✅), Bad (❌), or others (➖).
    """
    patient_info = processed_report.get("patient_info", {})
    results = processed_report.get("results", {})

    # Print basic patient info
    print("=== PATIENT INFORMATION ===")
    print(f"Name       : {patient_info.get('name', 'N/A')}")
    print(f"Age        : {patient_info.get('age', 'N/A')}")
    print(f"Sex        : {patient_info.get('sex', 'N/A')}")
    print(f"Report Date: {patient_info.get('report_date', 'N/A')}")
    print("-" * 60)

    # Go through categories
    for category_name, category_data in results.items():
        category_status = category_data.get("category_status", "N/A")
        category_summary = category_data.get("category_summary", "N/A")

        # Choose an icon based on category_status
        status_icon = "✅" if category_status.lower() == "good" else "❌" if category_status.lower() == "bad" else "➖"
        
        print(f"\n=== {category_name.upper()} {status_icon} ===")
        print(f"Category Status : {category_status}")
        print("Category Summary:")
        print(f"  {category_summary}\n")

        # Print each test in this category
        for test in category_data.get("tests", []):
            marker_label = test.get("marker_label", "Unknown Marker")
            value = test.get("value", "N/A")
            classification = test.get("classification", "N/A")
            range_applied = test.get("range_applied", "N/A")
            #interpretation = test.get("interpretation", "No interpretation.")

            # Decide which icon to print
            if classification.lower() == "good":
                cls_icon = "✅"
            elif classification.lower() == "bad":
                cls_icon = "❌"
            else:
                cls_icon = "➖"

            print(f"- Marker        : {marker_label}")
            print(f"  Value         : {value}")
            print(f"  Classification: {classification} {cls_icon}")
            print(f"  Reference     : {range_applied}")
           # print(f"  Interpretation: {interpretation}\n")

# def save_augmented_json(processed_report, filename="/tmp/output_opinion.json"):
#     """
#     Saves the augmented report (with interpretations and summaries)
#     to a JSON file called 'output_opinion.json' by default.
#     """
#     with open(filename, "w") as f:
#         json.dump(processed_report, f, indent=2)

def save_augmented_json(processed_report, filename="output_opinion.json"):
    # Detect execution environment
    if os.name == "nt":  # Windows / local
        base_dir = os.getcwd()
        # AWS Lambda / Linux
    else:  
        base_dir = tempfile.gettempdir()  # resolves to /tmp

    file_path = os.path.join(base_dir, filename)

    with open(file_path, "w") as f:
        json.dump(processed_report, f, indent=2)

    return file_path

def process_lab_report(xml_url):
    """
    Processes the lab report by:
      1) Parsing the XML data.
      2) Classifying test results.
      3) Adding interpretations and summaries.
      4) Printing a formatted report.
      5) Saving the augmented JSON.
      
    This function can be called from another script.
    """

    # 1) Parse XML and extract relevant data
    parsed_data = parse_thyrocare_xml(xml_url)

    # 2) Classify the extracted test results
    classified_data = classify_all_tests(parsed_data)

    # 3) Generate JSON output
    report_json = create_json_output(classified_data)

    # 4) Add explanations and summaries
    augmented_report = add_interpretations_and_summaries(report_json)

    # 5) Print formatted report
    print_colored_report(augmented_report)

    # 6) Save the enhanced report
    save_augmented_json(augmented_report)

    return augmented_report



def main():
    """
    Main function that ties everything together:
      1) Reads the original report from 'output.json'.
      2) Adds interpretations and category summaries.
      3) Prints the report with icons in the terminal.
      4) Saves the augmented JSON to 'output_opinion.json'.
    """

    if len(sys.argv) < 2:
        print("Usage: python parse_thyrocare.py <XML_URL>")
        sys.exit(1)

    xml_url = sys.argv[1]

    # 1) Parse
    parsed_data = parse_thyrocare_xml(xml_url)


    # 2) Classify
    original_report = classify_all_tests(parsed_data)
    filled_in = create_json_output(original_report)

    # 3. Add interpretations and category summaries
    processed_report = add_interpretations_and_summaries(filled_in)

    # 4. Print the nicely formatted report
    print_colored_report(processed_report)

    # 5. Save the final augmented JSON
    save_augmented_json(processed_report, "output_opinion.json")


# Entry point for script execution
if __name__ == "__main__":
    main()
