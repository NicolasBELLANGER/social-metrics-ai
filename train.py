import json
import os

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split

from db.connection import get_connection
from db.seed import seed_if_empty, sync_missing_tweets

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "models")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
POSITIVE_MODEL_PATH = os.path.join(MODEL_DIR, "positive_model.joblib")
NEGATIVE_MODEL_PATH = os.path.join(MODEL_DIR, "negative_model.joblib")

MODEL_PARAMS = {
    "max_iter": 2000,
    "random_state": 42,
    "class_weight": "balanced",
    "C": 50.0,
}


def load_tweets_from_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT text, positive, negative FROM tweets")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        raise ValueError("Aucun tweet en base. Vérifiez le seed.")

    texts = [row[0] for row in rows]
    y_positive = np.array([row[1] for row in rows])
    y_negative = np.array([row[2] for row in rows])

    return texts, y_positive, y_negative


def filter_sentiment_tweets(texts, y_positive, y_negative):
    """Exclut les tweets neutres (0, 0) de l'entraînement."""
    mask = (y_positive == 1) | (y_negative == 1)
    excluded = len(texts) - int(mask.sum())

    texts = [text for text, keep in zip(texts, mask) if keep]
    y_positive = y_positive[mask]
    y_negative = y_negative[mask]

    if excluded:
        print(f"{excluded} tweet(s) neutre(s) exclu(s) de l'entraînement.")

    if len(texts) < 4:
        raise ValueError("Pas assez de tweets annotés (positif ou négatif) pour entraîner.")

    return texts, y_positive, y_negative


def compute_class_metrics(y_test, y_pred):
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred, labels=[0, 1], zero_division=0
    )
    return {
        "class_0": {
            "precision": float(precision[0]),
            "recall": float(recall[0]),
            "f1": float(f1[0]),
            "support": int(support[0]),
        },
        "class_1": {
            "precision": float(precision[1]),
            "recall": float(recall[1]),
            "f1": float(f1[1]),
            "support": int(support[1]),
        },
    }


def evaluate_model(X_train, X_test, y_train, y_test, label_name):
    model = LogisticRegression(**MODEL_PARAMS)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = compute_class_metrics(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])

    print(f"\n=== Modèle {label_name} (évaluation) ===")
    print(classification_report(y_test, y_pred, zero_division=0))
    for class_name, class_label in [("class_0", "Non"), ("class_1", "Oui")]:
        data = metrics[class_name]
        print(
            f"Classe {class_label} — Précision: {data['precision']:.3f}, "
            f"Rappel: {data['recall']:.3f}, F1: {data['f1']:.3f}"
        )

    return metrics, cm


def fit_production_model(X, y):
    model = LogisticRegression(**MODEL_PARAMS)
    model.fit(X, y)
    return model


def save_confusion_matrix(cm, title, filename):
    os.makedirs(REPORT_DIR, exist_ok=True)

    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.title(title)
    plt.xlabel("Prédit")
    plt.ylabel("Réel")
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, filename))
    plt.close()


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    seed_if_empty()
    sync_missing_tweets()

    texts, y_positive, y_negative = load_tweets_from_db()
    texts, y_positive, y_negative = filter_sentiment_tweets(
        texts, y_positive, y_negative
    )

    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 3),
        min_df=1,
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(texts)

    indices = np.arange(len(texts))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=0.2,
        random_state=42,
        stratify=y_positive,
    )

    X_train, X_test = X[train_idx], X[test_idx]
    y_pos_train, y_pos_test = y_positive[train_idx], y_positive[test_idx]
    y_neg_train, y_neg_test = y_negative[train_idx], y_negative[test_idx]

    pos_metrics, pos_cm = evaluate_model(
        X_train, X_test, y_pos_train, y_pos_test, "positif"
    )
    neg_metrics, neg_cm = evaluate_model(
        X_train, X_test, y_neg_train, y_neg_test, "négatif"
    )

    save_confusion_matrix(pos_cm, "Matrice de confusion - Positif", "confusion_positive.png")
    save_confusion_matrix(neg_cm, "Matrice de confusion - Négatif", "confusion_negative.png")

    positive_model = fit_production_model(X, y_positive)
    negative_model = fit_production_model(X, y_negative)

    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(positive_model, POSITIVE_MODEL_PATH)
    joblib.dump(negative_model, NEGATIVE_MODEL_PATH)

    report = {
        "positive": pos_metrics,
        "negative": neg_metrics,
    }

    report_path = os.path.join(REPORT_DIR, "metrics.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nModèles sauvegardés dans models/")
    print("Matrices de confusion dans reports/")
    print(f"Métriques JSON : {report_path}")


if __name__ == "__main__":
    main()
