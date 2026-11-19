
from services.medical_entity_extractor import extract_medical_entities


sample_text = """
SAMPLE MEDICAL REPORT
Patient: Demo Patient
Medicine: Sample Medicine
Dosage: 0.5 mg
Frequency: Twice daily
Duration: Five days
Instructions: Take after food.
"""

result = extract_medical_entities(sample_text)

print("EXTRACTED MEDICAL INFORMATION:")
for key, value in result["entities"].items():
    print(f"{key}: {value}")

print("\nMETHOD:", result["extraction_method"])
print("HUMAN VERIFICATION REQUIRED:",
      result["requires_human_verification"])

assert result["entities"]["medicine"] == ["Sample Medicine"]
assert result["entities"]["dosage"] == ["0.5 mg"]
assert result["entities"]["frequency"] == ["Twice daily"]
assert result["entities"]["duration"] == ["Five days"]

print("\nMEDICAL ENTITY EXTRACTION TEST PASSED!")
