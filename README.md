# DataPulse — AIORI Hackathon 3 | PS-019

**Problem statement:** Personal-Data Discovery and Privacy Evidence Inventory  
**Team:** Forge · **Team code:** A3-PS019-TC304  
**Institution:** Muthoot Institute of Technology and Science  
**Mentor:** Sheena Kurian K

## What it does

DataPulse is a beginner-friendly educational prototype that:
- scans CSV headers and SQLite table schemas using transparent rules plus an ML classifier for five candidate data classes;
- automatically predicts on every CSV upload and uses high-confidence column-name predictions/rule labels as pseudo-labels for periodic retraining;
- displays the model type, training-example count, automatic-label count, detection method and prediction confidence;
- checks whether each detected class has purpose and retention metadata;
- produces a field inventory, metadata-gap report, scan summary, and separate evaluation evidence JSON;
- evaluates a 43-field manually labelled synthetic set and reports overall plus per-class precision/recall, false positives, and missed detections;
- provides a web dashboard and CSV/JSON downloads.

**Important limitation:** this is a rule-based discovery aid, not a legal compliance checker or proof that a field contains personal data. Every candidate should be reviewed by a human. The demo scans column names only and does not export row values.

## Requirements

- Python 3.10 or newer
- pip
- A browser

## Run on Windows

1. Extract the ZIP.
2. Open PowerShell in the `PS019_DataPulse_Advanced` folder.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Run the dashboard:

   ```powershell
   python app.py
   ```

6. Open `http://127.0.0.1:5000`.
7. Click **Run demo scan**. The dashboard will show the findings and metadata gaps.
8. Download the CSV/JSON evidence from the Export evidence section.

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and then `.\.venv\Scripts\python.exe app.py`.

## Run tests

From the project folder:

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
PS019_DataPulse_Advanced/
├── app.py                   # Flask dashboard routes
├── scanner.py               # CSV/SQLite scanning, rules and metrics
├── ml_model.py              # TF-IDF classifier and automatic self-training
├── requirements.txt
├── data/
│   ├── customers.csv        # Synthetic CSV rows
│   ├── demo.db              # Synthetic SQLite database
│   ├── metadata.json        # Purpose and retention declarations
│   └── labelled_fields.csv  # Manual labels for evaluation
├── templates/index.html     # Dashboard layout
├── static/style.css         # Dashboard styling
├── tests/test_scanner.py    # 11 automated tests
├── reports/                 # Scan and evaluation evidence outputs
├── docs/
│   ├── project_report.md
│   ├── reflection.md
│   └── demo_script_hinglish.md
└── README.md
```

## How the scanner works

1. It reads column names from the CSV header or SQLite schema.
2. It compares names against configurable regular-expression rules in `scanner.py`.
3. For each candidate, it checks `data/metadata.json` for purpose and retention.
4. Missing entries are marked as metadata gaps.
5. Results are written to `reports/inventory.csv`, `reports/metadata_gaps.csv`, and `reports/metrics.json`.

## Customising detection rules

Open `scanner.py` and edit the `RULES` dictionary. The five classes are full name, email, phone, address and passport number. The scanner recognises some aliases and explicitly ignores a few known non-personal names such as `email_template`. It still misses unfamiliar names such as `house_location` and `travel_document_code`; these examples appear in the evaluation output. Results are based on a small synthetic set and are not real-world performance guarantees.

## Safety and privacy notes

- Use synthetic data or data you are authorised to assess.
- Do not upload real personal data to a public demo.
- This prototype does not perform external network calls.
- The Flask development server is for local demonstration only; do not expose it to the public internet.

## Automatic ML learning

DataPulse trains a character n-gram TF-IDF + Logistic Regression model from the bundled labelled field-name examples. Each CSV upload triggers prediction on column names only. Existing rule matches can add trusted synthetic labels; model-generated pseudo-labels are accepted only at confidence >= 0.90. The model retrains after at least three new accepted labels. Predictions below 0.65 confidence are left unclassified by ML. The training model and pseudo-label pool are stored locally in `models/` and `data/auto_labelled_fields.csv`.

This is an experimental self-training loop: pseudo-labels can be wrong and can reinforce mistakes. The model does not inspect CSV row values, and automatic retraining does not mean the predictions are ground truth. Keep backups of the labelled dataset and inspect model outputs during development. The 43-field evaluation report remains separate from the expanded ML training seed set so training examples are not silently counted as evaluation results.
