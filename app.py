from pathlib import Path
import json
import csv
import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from scanner import scan_csv, scan_sqlite, save_results, calculate_metrics
from ml_model import load_model, learn_from_upload, model_status

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "datapulse-demo-secret-change-me"


def load_demo_results():
    inventory_path = REPORT_DIR / "inventory.csv"
    gaps_path = REPORT_DIR / "metadata_gaps.csv"
    metrics_path = REPORT_DIR / "metrics.json"
    evaluation_path = REPORT_DIR / "evaluation_metrics.json"
    if inventory_path.exists() and gaps_path.exists() and metrics_path.exists():
        import csv
        with inventory_path.open(newline="", encoding="utf-8") as f:
            inventory = list(csv.DictReader(f))
        with gaps_path.open(newline="", encoding="utf-8") as f:
            gaps = list(csv.DictReader(f))
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8")) if evaluation_path.exists() else {}
        return inventory, gaps, metrics, evaluation
    return [], [], {"candidate_fields": 0, "metadata_gaps": 0, "classes_found": []}, {}


@app.route("/")
def index():
    # Build/load the local model automatically the first time the dashboard opens.
    load_model()
    inventory, gaps, metrics, evaluation = load_demo_results()
    return render_template("index.html", inventory=inventory, gaps=gaps, metrics=metrics, evaluation=evaluation, ml_status=model_status())


@app.route("/scan-demo", methods=["POST"])
def scan_demo():
    source = request.form.get("source", "both")
    metadata_path = DATA_DIR / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    results = []
    model = load_model()
    if source in ("csv", "both"):
        results.extend(scan_csv(DATA_DIR / "customers.csv", metadata, source_name="customers.csv", ml_model=model))
    if source in ("sqlite", "both"):
        results.extend(scan_sqlite(DATA_DIR / "demo.db", metadata, table_name="customers", source_name="demo.db", ml_model=model))
    save_results(results, REPORT_DIR)
    evaluation = calculate_metrics([], DATA_DIR / "labelled_fields.csv")
    (REPORT_DIR / "evaluation_metrics.json").write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
    flash(f"Demo scan complete: {len(results)} candidate fields found.", "success")
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload():
    uploaded = request.files.get("dataset")
    if not uploaded or not uploaded.filename:
        flash("Please choose a CSV file first.", "error")
        return redirect(url_for("index"))
    if not uploaded.filename.lower().endswith(".csv"):
        flash("Only CSV uploads are supported in this demo.", "error")
        return redirect(url_for("index"))
    safe_name = Path(uploaded.filename).name
    target = UPLOAD_DIR / safe_name
    uploaded.save(target)
    metadata = json.loads((DATA_DIR / "metadata.json").read_text(encoding="utf-8"))
    # Train only on column names. CSV row values are never used by the ML pipeline.
    with target.open("r", newline="", encoding="utf-8-sig") as handle:
        field_names = next(csv.reader(handle), [])
    model = load_model()
    model, learning = learn_from_upload(field_names, model)
    results = scan_csv(target, metadata, source_name=safe_name, ml_model=model)
    save_results(results, REPORT_DIR)
    evaluation = calculate_metrics([], DATA_DIR / "labelled_fields.csv")
    (REPORT_DIR / "evaluation_metrics.json").write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
    flash(f"Upload scan complete: {len(results)} candidate fields found. ML auto-learning added {learning['new_auto_labels']} high-confidence examples; retrained: {learning['retrained']}.", "success")
    return redirect(url_for("index"))


@app.route("/export/<kind>")
def export(kind):
    allowed = {"inventory": "inventory.csv", "gaps": "metadata_gaps.csv", "metrics": "metrics.json", "evaluation": "evaluation_metrics.json", "ml_status": "ml_status.json"}
    if kind not in allowed:
        flash("Unknown export type.", "error")
        return redirect(url_for("index"))
    path = REPORT_DIR / allowed[kind]
    if kind == "ml_status":
        path.write_text(json.dumps(model_status(), indent=2), encoding="utf-8")
    if not path.exists():
        flash("No report exists yet. Run a scan first.", "error")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
