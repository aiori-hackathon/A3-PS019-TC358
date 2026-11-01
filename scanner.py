"""Beginner-friendly personal-data field scanner for synthetic CSV and SQLite data."""
import csv
import json
import re
import sqlite3
from pathlib import Path

# Rules are transparent name-based hints, not proof that a field is personal data.
RULES = {
    "full_name": ("Full name", re.compile(r"(^|_)(full_name|fullname|name|customer_name|client_name|contact_name|account_holder)($|_)")),
    "email": ("Email", re.compile(r"(^|_)(email|e_mail|email_address|mail_id|mail_address|contact_email)($|_)")),
    "phone": ("Phone", re.compile(r"(^|_)(phone|mobile|telephone|phone_no|mobile_no|msisdn|contact_number)($|_)")),
    "address": ("Postal address", re.compile(r"(^|_)(address|postal_address|street_address|home_addr|mailing_addr|addr_line[0-9]*|address_line[0-9]*)($|_)")),
    "passport_number": ("Passport number", re.compile(r"(^|_)(passport|passport_no|passport_id|travel_doc_no)($|_)")),
}

# Common non-personal columns that contain a sensitive-looking word.
# Keeping these exclusions explicit makes false-positive handling easy to explain.
NON_PERSONAL_EXCEPTIONS = {
    "email_template", "email_status", "email_verified", "phone_model",
    "phone_type", "address_template", "name_format", "passport_template",
}


def normalize_field_name(field_name):
    """Make names such as 'Mail ID' and 'mail-id' comparable."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", str(field_name).strip().lower())
    return re.sub(r"_+", "_", normalized).strip("_")


def classify_field(field_name):
    """Return a candidate data class, or None when no rule matches."""
    normalized = normalize_field_name(field_name)
    if normalized in NON_PERSONAL_EXCEPTIONS:
        return None
    for data_class, (_, pattern) in RULES.items():
        if pattern.search(normalized):
            return data_class
    return None


def metadata_status(data_class, metadata):
    """Check whether purpose and retention are documented for a data class."""
    entry = metadata.get(data_class, {})
    purpose = str(entry.get("purpose", "")).strip()
    retention = str(entry.get("retention", "")).strip()
    missing = []
    if not purpose:
        missing.append("purpose")
    if not retention:
        missing.append("retention")
    return purpose, retention, "; ".join(missing)


def make_finding(source, table, field, data_class, metadata, detection_method="rule-based", confidence=1.0):
    purpose, retention, missing = metadata_status(data_class, metadata)
    return {
        "source": source, "table": table, "field": field,
        "data_class": data_class, "purpose": purpose,
        "retention": retention, "metadata_gap": missing,
        "rule": detection_method + "; human review required",
        "confidence": round(float(confidence), 4),
    }


def scan_csv(csv_path, metadata, source_name=None, ml_model=None):
    """Inspect CSV headers only; do not read or export personal values."""
    csv_path = Path(csv_path)
    findings = []
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for field in (reader.fieldnames or []):
            data_class = classify_field(field)
            method = "rule-based"
            confidence = 1.0
            if not data_class and ml_model is not None:
                from ml_model import predict_field
                data_class, confidence = predict_field(field, ml_model)
                method = "ML prediction"
            if data_class:
                findings.append(make_finding(source_name or csv_path.name, "CSV", field, data_class, metadata, method, confidence))
    return findings


def scan_sqlite(db_path, metadata, table_name="customers", source_name=None, ml_model=None):
    """Inspect SQLite column names only; values are never selected."""
    db_path = Path(db_path)
    findings = []
    connection = sqlite3.connect(str(db_path))
    try:
        safe_table = table_name.replace('"', '""')
        columns = connection.execute(f'PRAGMA table_info("{safe_table}")').fetchall()
        for column in columns:
            field = column[1]
            data_class = classify_field(field)
            method = "rule-based"
            confidence = 1.0
            if not data_class and ml_model is not None:
                from ml_model import predict_field
                data_class, confidence = predict_field(field, ml_model)
                method = "ML prediction"
            if data_class:
                findings.append(make_finding(source_name or db_path.name, table_name, field, data_class, metadata, method, confidence))
    finally:
        connection.close()
    return findings


def calculate_metrics(findings, labelled_path):
    """Calculate binary and per-class metrics from manually labelled field names.

    Expected CSV columns: source, field, is_personal, expected_class.
    Blank expected_class means the field is labelled non-personal for this test.
    """
    with Path(labelled_path).open("r", newline="", encoding="utf-8-sig") as handle:
        labels = list(csv.DictReader(handle))

    # The labelled set evaluates the detector on the named field, independent of source paths.
    evaluated = []
    for row in labels:
        expected_personal = row.get("is_personal", "").strip().lower() == "true"
        expected_class = row.get("expected_class", "").strip() or None
        predicted_class = classify_field(row["field"])
        evaluated.append({
            "source": row.get("source", "labelled test set"),
            "field": row["field"],
            "expected_personal": expected_personal,
            "expected_class": expected_class,
            "predicted_class": predicted_class,
        })

    tp = sum(item["expected_personal"] and item["predicted_class"] is not None for item in evaluated)
    fp = sum((not item["expected_personal"]) and item["predicted_class"] is not None for item in evaluated)
    fn = sum(item["expected_personal"] and item["predicted_class"] is None for item in evaluated)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    per_class = {}
    for data_class in RULES:
        class_tp = sum(item["expected_class"] == data_class and item["predicted_class"] == data_class for item in evaluated)
        class_fp = sum(item["predicted_class"] == data_class and item["expected_class"] != data_class for item in evaluated)
        class_fn = sum(item["expected_class"] == data_class and item["predicted_class"] != data_class for item in evaluated)
        per_class[data_class] = {
            "true_positives": class_tp,
            "false_positives": class_fp,
            "false_negatives": class_fn,
            "precision": round(class_tp / (class_tp + class_fp), 3) if class_tp + class_fp else 0.0,
            "recall": round(class_tp / (class_tp + class_fn), 3) if class_tp + class_fn else 0.0,
        }

    false_positives = [item["field"] for item in evaluated if not item["expected_personal"] and item["predicted_class"]]
    missed = [item["field"] for item in evaluated if item["expected_personal"] and not item["predicted_class"]]
    wrong_class = [item["field"] for item in evaluated if item["expected_class"] and item["predicted_class"] and item["expected_class"] != item["predicted_class"]]
    return {
        "test_set_size": len(evaluated),
        "labelled_personal_fields": sum(item["expected_personal"] for item in evaluated),
        "labelled_non_personal_fields": sum(not item["expected_personal"] for item in evaluated),
        "true_positives": tp, "false_positives": fp, "false_negatives": fn,
        "precision": round(precision, 3), "recall": round(recall, 3),
        "per_class": per_class,
        "false_positive_examples": false_positives,
        "missed_detection_examples": missed,
        "wrong_class_examples": wrong_class,
        "note": "Results apply only to this small manually labelled synthetic test set; they are not a real-world performance guarantee."
    }


def save_results(findings, output_dir):
    """Write inventory, metadata gaps and scan summary to disk."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    columns = ["source", "table", "field", "data_class", "purpose", "retention", "metadata_gap", "rule", "confidence"]
    with (output_dir / "inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(findings)
    gaps = [row for row in findings if row["metadata_gap"]]
    with (output_dir / "metadata_gaps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(gaps)
    metrics = {
        "candidate_fields": len(findings),
        "metadata_gaps": len(gaps),
        "classes_found": sorted({row["data_class"] for row in findings}),
        "note": "Candidate matches only; human review is required. Evaluation metrics are available separately."
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
