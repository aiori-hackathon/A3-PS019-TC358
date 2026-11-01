import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from scanner import classify_field, normalize_field_name, metadata_status, scan_csv, scan_sqlite, save_results, calculate_metrics

ROOT = Path(__file__).resolve().parents[1]


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.metadata = json.loads((ROOT / "data" / "metadata.json").read_text(encoding="utf-8"))

    def test_detects_standard_email(self):
        self.assertEqual(classify_field("email"), "email")

    def test_detects_unusual_aliases(self):
        self.assertEqual(classify_field("Mail ID"), "email")
        self.assertEqual(classify_field("mobile-no"), "phone")
        self.assertEqual(classify_field("addr_line1"), "address")
        self.assertEqual(classify_field("travel_doc_no"), "passport_number")

    def test_normalizes_field_names(self):
        self.assertEqual(normalize_field_name("Mail ID"), "mail_id")

    def test_ignores_non_personal_field(self):
        self.assertIsNone(classify_field("membership_tier"))

    def test_reduces_known_false_positives(self):
        self.assertIsNone(classify_field("email_template"))
        self.assertIsNone(classify_field("phone_model"))
        self.assertIsNone(classify_field("address_template"))

    def test_documents_known_missed_detection(self):
        # This is intentionally unsupported so evaluation can expose a limitation.
        self.assertIsNone(classify_field("house_location"))

    def test_reports_missing_metadata(self):
        purpose, retention, missing = metadata_status("phone", self.metadata)
        self.assertTrue(purpose)
        self.assertEqual(retention, "")
        self.assertIn("retention", missing)

    def test_scans_csv_headers(self):
        findings = scan_csv(ROOT / "data" / "customers.csv", self.metadata)
        self.assertTrue(any(row["field"] == "email" for row in findings))
        self.assertFalse(any(row["field"] == "membership_tier" for row in findings))

    def test_scans_sqlite_schema(self):
        findings = scan_sqlite(ROOT / "data" / "demo.db", self.metadata)
        self.assertTrue(any(row["field"] == "passport_number" for row in findings))

    def test_saves_inventory_and_gaps(self):
        findings = scan_csv(ROOT / "data" / "customers.csv", self.metadata)
        with tempfile.TemporaryDirectory() as tmp:
            metrics = save_results(findings, tmp)
            self.assertTrue((Path(tmp) / "inventory.csv").exists())
            self.assertTrue((Path(tmp) / "metadata_gaps.csv").exists())
            self.assertEqual(metrics["candidate_fields"], len(findings))

    def test_evaluation_reports_per_class_and_errors(self):
        metrics = calculate_metrics([], ROOT / "data" / "labelled_fields.csv")
        self.assertEqual(metrics["test_set_size"], 43)
        self.assertIn("email", metrics["per_class"])
        self.assertIn("house_location", metrics["missed_detection_examples"])
        self.assertGreaterEqual(metrics["precision"], 0)
        self.assertGreaterEqual(metrics["recall"], 0)

    def test_ml_model_trains_and_returns_confidence(self):
        from ml_model import load_model, predict_field
        model = load_model()
        prediction, confidence = predict_field("travel_document_code", model)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertTrue(prediction is None or isinstance(prediction, str))


if __name__ == "__main__":
    unittest.main()
