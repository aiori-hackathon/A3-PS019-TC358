"""Automatic ML helper for DataPulse. Trains on field names, never CSV row values."""
import csv
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "field_classifier.joblib"
TRAINED_COUNT_PATH = MODEL_DIR / "trained_pseudo_count.json"
PSEUDO_PATH = DATA_DIR / "auto_labelled_fields.csv"
BASE_LABELS = DATA_DIR / "labelled_fields.csv"
SEED_LABELS = DATA_DIR / "ml_training_seed.csv"

# Predictions below this confidence are shown as unknown, not forced into a class.
PREDICTION_THRESHOLD = 0.65
# Only very confident predictions can enter the automatic training pool.
LEARNING_THRESHOLD = 0.90


def read_training_rows():
    rows = []
    for path in (BASE_LABELS, SEED_LABELS, PSEUDO_PATH):
        if not path.exists():
            continue
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                field = row.get("field", "").strip()
                if not field:
                    continue
                label = row.get("expected_class", "").strip() or "non_personal"
                rows.append((field, label))
    return rows


def build_pipeline():
    return Pipeline([
        ("vectorizer", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), lowercase=True, sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=1500, class_weight="balanced", random_state=42)),
    ])


def train_model():
    rows = read_training_rows()
    if len(rows) < 5:
        raise ValueError("Not enough labelled field names to train the model.")
    model = build_pipeline()
    model.fit([row[0] for row in rows], [row[1] for row in rows])
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return model


def load_model():
    if MODEL_PATH.exists():
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            # Rebuild an incompatible or damaged local model from the bundled labels.
            return train_model()
    return train_model()


def predict_field(field_name, model=None):
    model = model or load_model()
    probabilities = model.predict_proba([str(field_name)])[0]
    classes = model.named_steps["classifier"].classes_
    best_index = int(probabilities.argmax())
    label = str(classes[best_index])
    confidence = float(probabilities[best_index])
    if confidence < PREDICTION_THRESHOLD:
        return None, confidence
    return (None if label == "non_personal" else label), confidence


def learn_from_upload(field_names, model=None):
    """Add only high-confidence pseudo-labels; retrain after 3 new examples."""
    model = model or load_model()
    PSEUDO_PATH.parent.mkdir(exist_ok=True)
    existing = set()
    for label_path in (BASE_LABELS, SEED_LABELS, PSEUDO_PATH):
        if label_path.exists():
            with label_path.open("r", newline="", encoding="utf-8-sig") as handle:
                existing.update(row["field"].strip().lower() for row in csv.DictReader(handle))
    if PSEUDO_PATH.exists():
        with PSEUDO_PATH.open("r", newline="", encoding="utf-8-sig") as handle:
            existing = {row["field"].strip().lower() for row in csv.DictReader(handle)}

    new_rows = []
    for field in field_names:
        field = str(field).strip()
        if not field or field.lower() in existing:
            continue
        # Existing transparent scanner rules can supply trusted synthetic labels.
        from scanner import classify_field
        rule_label = classify_field(field)
        if rule_label:
            label, confidence = rule_label, 1.0
        else:
            label, confidence = predict_field(field, model)
        if confidence >= LEARNING_THRESHOLD:
            new_rows.append({"source": "automatic_upload", "field": field,
                             "is_personal": str(label is not None).lower(),
                             "expected_class": label or "", "confidence": round(confidence, 4)})
            existing.add(field.lower())

    if new_rows:
        file_exists = PSEUDO_PATH.exists()
        with PSEUDO_PATH.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["source", "field", "is_personal", "expected_class", "confidence"])
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_rows)

    retrained = False
    pseudo_total = 0
    if PSEUDO_PATH.exists():
        with PSEUDO_PATH.open("r", newline="", encoding="utf-8-sig") as handle:
            pseudo_total = sum(1 for _ in csv.DictReader(handle))
    last_trained = 0
    if TRAINED_COUNT_PATH.exists():
        try:
            last_trained = int(json.loads(TRAINED_COUNT_PATH.read_text(encoding="utf-8")).get("count", 0))
        except (ValueError, json.JSONDecodeError):
            last_trained = 0
    if pseudo_total - last_trained >= 3:
        model = train_model()
        TRAINED_COUNT_PATH.write_text(json.dumps({"count": pseudo_total}, indent=2), encoding="utf-8")
        retrained = True
    return model, {"new_auto_labels": len(new_rows), "retrained": retrained,
                   "training_examples": len(read_training_rows())}


def model_status():
    auto_count = 0
    if PSEUDO_PATH.exists():
        with PSEUDO_PATH.open("r", newline="", encoding="utf-8-sig") as handle:
            auto_count = sum(1 for _ in csv.DictReader(handle))
    return {"model_name": "TF-IDF + Logistic Regression", "model_ready": MODEL_PATH.exists(),
            "prediction_threshold": PREDICTION_THRESHOLD,
            "auto_learning_threshold": LEARNING_THRESHOLD,
            "training_examples": len(read_training_rows()),
            "auto_labelled_examples": auto_count}
