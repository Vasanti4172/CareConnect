
from services.text_preprocessor import clean_extracted_text


sample_text = """
    SAMPLE MEDICAL REPORT


    Patient: Demo Patient
    Medicine: Sample Medicine
    Dosage:   0.5 mg
    Frequency: Twice daily

    Duration: Five days
"""

result = clean_extracted_text(sample_text)

print("CLEANED TEXT:")
print(result["cleaned_text"])

print("\nCHARACTER COUNT:", result["character_count"])
print("LINE COUNT:", result["line_count"])
print("IS EMPTY:", result["is_empty"])

# Important: medically relevant values must remain unchanged.
assert "0.5 mg" in result["cleaned_text"]
assert "Twice daily" in result["cleaned_text"]
assert "Five days" in result["cleaned_text"]

print("\nTEXT PREPROCESSING TEST PASSED!")

