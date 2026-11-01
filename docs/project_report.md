# DataPulse — Project Report

## 1. Abstract
DataPulse is an educational prototype for the AIORI Hackathon 3 Cyber Security Track problem statement PS-019, Personal-Data Discovery and Privacy Evidence Inventory. It scans synthetic CSV and SQLite schemas to identify candidate personal-data fields, then checks whether a declared purpose and retention period are recorded for each detected class.

## 2. Problem
Organisations can have personal-data fields spread across multiple files and databases. If a field has no documented purpose or retention period, a reviewer may not have enough evidence to assess whether its handling is appropriate. Manual discovery can be time-consuming.

## 3. Objective
- Discover candidate personal-data fields in a synthetic CSV file and an SQL database.
- Support five predefined classes: full name, email, phone, address and passport number.
- Link findings to declared purpose and retention metadata.
- Export an inventory and a list of metadata gaps for human review.
- Evaluate the rules against a small manually labelled test set.

## 4. Methodology
The scanner reads CSV column headers and SQLite table schema information; it does not need to read or export data-row values for discovery. Field names are compared with simple regular-expression rules. Each detected class is matched with `data/metadata.json`. A missing purpose or retention entry is recorded as a gap. The application exports `inventory.csv`, `metadata_gaps.csv`, and `metrics.json`. It also creates `evaluation_metrics.json` with overall and per-class precision/recall, false-positive examples, and missed-detection examples from a 43-field manually labelled synthetic test set.

## 5. Technology
- Python for scanning and evaluation.
- SQLite for a small local SQL dataset.
- Flask for the web dashboard.
- HTML and CSS for the interface.
- Python `unittest` for automated tests.

## 6. Dataset
The project includes synthetic customer records in `data/customers.csv` and `data/demo.db`. Names and contact details are fabricated for demonstration. `data/labelled_fields.csv` provides manual field-level labels used for a simple precision/recall calculation.

## 7. Evidence and outputs
The application displays candidate fields, data classes, purpose, retention and review status. It also lists metadata gaps. Exports are generated in the `reports/` folder after a scan. Test results can be reproduced with `python -m unittest discover -s tests -v`.

## 8. Limitations
- Detection is based mainly on field names and may miss unfamiliar names.
- A field-name match is only a candidate; it is not proof that a field contains personal data.
- The 43-field synthetic labelled set is small and cannot establish performance on real organisations' data. In this sample the detector has precision 1.000 and recall 0.923; it misses `travel_document_code` and `house_location`. These are sample-specific results, not a real-world performance guarantee.
- Metadata is supplied in a local JSON file rather than obtained from a production governance platform.
- The dashboard is a local educational prototype and is not production-hardened.

## 9. Future work
- Add more configurable data classes and explain each match.
- Support safe review workflows and reviewer notes.
- Expand and independently review the labelled dataset; track false positives, missed detections, and class-wise precision/recall.
- Add database connectors with explicit allowlists and read-only access.
- Add authentication, audit logging and deployment hardening before any real deployment.

## 10. Conclusion
DataPulse demonstrates a simple workflow for finding candidate personal-data fields and highlighting missing purpose/retention documentation. It turns schema discovery into a reviewable evidence inventory while keeping human judgement central.


## Machine-learning extension

The updated prototype uses character n-gram TF-IDF with Logistic Regression to classify field names. Transparent rule matches take precedence; the ML model is used for names not matched by a rule. Each CSV upload triggers predictions from header names only. Predictions with confidence of at least 0.90 may enter a local pseudo-labelled training pool. The model retrains after at least three newly accepted examples. Predictions below 0.65 confidence remain unclassified by ML. The original 43-field labelled evaluation set is separate from the additional curated ML training seed data.

This automatic self-training design does not use personal row values. Pseudo-labels may be wrong, so the system is experimental and not a source of ground truth. Detection method and confidence are shown in the dashboard.
