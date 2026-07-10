import os
import joblib
from flask import Flask, request, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
POSITIVE_MODEL_PATH = os.path.join(MODEL_DIR, "positive_model.joblib")
NEGATIVE_MODEL_PATH = os.path.join(MODEL_DIR, "negative_model.joblib")

_vectorizer = None
_positive_model = None
_negative_model = None


def _load_models():
    global _vectorizer, _positive_model, _negative_model
    if _vectorizer is None:
        paths = [VECTORIZER_PATH, POSITIVE_MODEL_PATH, NEGATIVE_MODEL_PATH]
        if not all(os.path.exists(p) for p in paths):
            raise FileNotFoundError(
                "Modèles introuvables. Lance d'abord : python train.py"
            )
        _vectorizer = joblib.load(VECTORIZER_PATH)
        _positive_model = joblib.load(POSITIVE_MODEL_PATH)
        _negative_model = joblib.load(NEGATIVE_MODEL_PATH)


def predict_sentiment(text: str) -> float:
    """Score entre -1 (très négatif) et 1 (très positif)."""
    _load_models()

    vec = _vectorizer.transform([text])
    proba_positive = _positive_model.predict_proba(vec)[0][1]
    proba_negative = _negative_model.predict_proba(vec)[0][1]

    score = proba_positive - proba_negative

    # Atténue les scores faibles quand aucun signal clair (tweet neutre)
    if proba_positive < 0.35 and proba_negative < 0.35:
        score *= 0.3

    return round(float(score), 4)


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)

    if data is None or not isinstance(data, list):
        return jsonify({"error": "Le corps de la requête doit être une liste de chaînes de caractères (string[])."}), 400

    if len(data) == 0:
        return jsonify({"error": "La liste de tweets ne peut pas être vide."}), 400

    if not all(isinstance(tweet, str) for tweet in data):
        return jsonify({"error": "Chaque élément de la liste doit être une chaîne de caractères."}), 400

    try:
        results = {tweet: predict_sentiment(tweet) for tweet in data}
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503

    return jsonify(results)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)