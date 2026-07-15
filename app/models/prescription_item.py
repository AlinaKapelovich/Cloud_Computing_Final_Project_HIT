"""PrescriptionItem — a single medication line inside a prescription.

Items are stored as embedded documents inside the parent prescription document
(a natural fit for MongoDB's document model), so there is no separate collection.
This module provides helpers to build and validate item dictionaries.
"""


def build_item(data: dict) -> dict:
    """Normalise one raw item into a clean dictionary."""
    return {
        "drug_name": (data.get("drug_name") or "").strip(),
        "dosage": (data.get("dosage") or "").strip(),
        "frequency": (data.get("frequency") or "").strip(),
        "duration": (data.get("duration") or "").strip(),
        "notes": (data.get("notes") or "").strip(),
    }


def build_items_from_lists(drug_names, dosages, frequencies, durations, notes) -> list:
    """Build a list of items from parallel form arrays, skipping empty rows."""
    items = []
    for index, name in enumerate(drug_names or []):
        if not (name or "").strip():
            continue  # ignore blank rows added by the UI.
        items.append(
            build_item(
                {
                    "drug_name": name,
                    "dosage": _at(dosages, index),
                    "frequency": _at(frequencies, index),
                    "duration": _at(durations, index),
                    "notes": _at(notes, index),
                }
            )
        )
    return items


def _at(seq, index: int) -> str:
    if seq and index < len(seq):
        return seq[index]
    return ""
