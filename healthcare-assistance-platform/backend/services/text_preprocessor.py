
import re


def clean_extracted_text(raw_text: str) -> dict:
    """
    Normalize extracted medical text without changing
    medically significant numbers, units, or instructions.
    """

    if not isinstance(raw_text, str):
        raise TypeError("Input text must be a string.")

    # Preserve the original input outside this function.
    cleaned_text = raw_text

    # Normalize Windows and old Mac line endings.
    cleaned_text = cleaned_text.replace("\r\n", "\n")
    cleaned_text = cleaned_text.replace("\r", "\n")

    # Remove null characters sometimes found in extracted text.
    cleaned_text = cleaned_text.replace("\x00", "")

    # Remove trailing spaces from each line.
    lines = [line.strip() for line in cleaned_text.split("\n")]

    # Replace tabs and repeated spaces within each line.
    lines = [re.sub(r"[ \t]+", " ", line) for line in lines]

    # Keep at most one blank line between content blocks.
    normalized_lines = []
    previous_line_was_blank = False

    for line in lines:
        is_blank = not line.strip()

        if is_blank:
            if not previous_line_was_blank:
                normalized_lines.append("")
            previous_line_was_blank = True
        else:
            normalized_lines.append(line)
            previous_line_was_blank = False

    cleaned_text = "\n".join(normalized_lines).strip()

    return {
        "cleaned_text": cleaned_text,
        "character_count": len(cleaned_text),
        "line_count": len(cleaned_text.splitlines()) if cleaned_text else 0,
        "is_empty": not bool(cleaned_text)
    }
