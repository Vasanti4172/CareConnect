
import re


def extract_medical_entities(text: str) -> dict:
    """
    Extract explicitly labelled medical information.
    Does not infer or recommend treatment.
    """

    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    patterns = {
        "patient_name": r"(?im)^\s*Patient(?:\s+Name)?\s*:\s*(.+)$",
        "medicine": r"(?im)^\s*(?:Medicine|Medication|Drug)\s*:\s*(.+)$",
        "dosage": r"(?im)^\s*(?:Dosage|Dose)\s*:\s*(.+)$",
        "frequency": r"(?im)^\s*(?:Frequency|How often)\s*:\s*(.+)$",
        "duration": r"(?im)^\s*(?:Duration|For)\s*:\s*(.+)$",
        "instructions": r"(?im)^\s*(?:Instructions|Advice)\s*:\s*(.+)$",
    }

    entities = {}

    for entity_name, pattern in patterns.items():
        matches = re.findall(pattern, text)

        # Keep the original text value; do not medically correct it.
        entities[entity_name] = [
            match.strip() for match in matches if match.strip()
        ]

    # Capture simple numeric dosage expressions where present.
    # These are observations, not dosage recommendations.
    dosage_pattern = (
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:mg|mcg|g|ml|mL|IU|units?)\b"
    )

    entities["dosage_values_found"] = re.findall(
        dosage_pattern, text, flags=re.IGNORECASE
    )

    return {
        "entities": entities,
        "extraction_method": "rule_based",
        "requires_human_verification": True
    }
