
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_KEYS = ["title", "industry", "skills", "context", "tenure", "recency", "bonus"]


def _normalize_join_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "candidate" in df.columns and "name" not in df.columns:
        df = df.rename(columns={"candidate": "name"})
    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.strip()
    if "candidate_id" in df.columns:
        df["candidate_id"] = df["candidate_id"].astype(str).str.strip()
    return df


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -50, 50)))


def _fit_logistic_np(X: np.ndarray, y: np.ndarray, lr: float = 0.1, epochs: int = 4000):
    w = np.zeros(X.shape[1], dtype="float32")
    b = 0.0
    for _ in range(epochs):
        preds = _sigmoid(X @ w + b)
        error = preds - y
        grad_w = (X.T @ error) / X.shape[0]
        grad_b = float(error.mean())
        w -= lr * grad_w
        b -= lr * grad_b
    return {"weights": w, "bias": float(b)}


def train(
    scores_path: str = "data/out/scores.json",
    labels_csv: str = "data/labels.csv",
    out_path: str = "models/trained/model.pkl",
):
    # Load scores, handling both new nested format and legacy flat format
    import json
    with open(scores_path) as f:
        scores_data = json.load(f)
    
    # Extract results array from new format, or use data directly for legacy format
    if isinstance(scores_data, dict) and "results" in scores_data:
        scores_list = scores_data["results"]
    elif isinstance(scores_data, list):
        scores_list = scores_data
    else:
        scores_list = [scores_data] if isinstance(scores_data, dict) else []
    
    if not scores_list:
        print("Skipping training: no candidate data found in scores file.")
        raise SystemExit(0)
    
    scores = _normalize_join_columns(pd.DataFrame(scores_list))
    try:
        labels_raw = pd.read_csv(labels_csv)
    except FileNotFoundError:
        print(
            f"Skipping training: labels file '{labels_csv}' not found. "
            "Create the file with at least a 'label' column and rerun."
        )
        raise SystemExit(0)

    labels = _normalize_join_columns(labels_raw)

    if "label" not in labels.columns:
        print(
            "Skipping training: labels file lacks 'label' column. "
            "Add labels to enable model fitting."
        )
        raise SystemExit(0)

    labels = labels.dropna(subset=["label"])
    if labels.empty:
        print(
            "Skipping training: no labeled rows detected. "
            "Ensure at least one row has a label value."
        )
        raise SystemExit(0)

    join_key = None
    if "candidate_id" in scores.columns and "candidate_id" in labels.columns:
        join_key = "candidate_id"
    elif "name" in scores.columns and "name" in labels.columns:
        join_key = "name"
    else:
        print(
            "Skipping training: labels and scores need a shared 'candidate_id' or 'name'."
        )
        raise SystemExit(0)

    df = scores.merge(labels[[join_key, "label"]], on=join_key, how="inner")

    X, y = [], []
    for _, row in df.iterrows():
        subs = {k: row.get(k, None) for k in FEATURE_KEYS}
        if subs["title"] is None and "subs" in row:
            subs = row["subs"] if isinstance(row["subs"], dict) else {}
        x = [float(subs.get(k, 0.0) or 0.0) for k in FEATURE_KEYS]
        X.append(np.array(x, dtype="float32"))
        y.append(int(row["label"]))

    if not X:
        print(
            "Skipping training: no overlap between score rows and labeled entries."
        )
        raise SystemExit(0)

    X = np.vstack(X)
    y = np.array(y, dtype="float32")

    model = _fit_logistic_np(X, y)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump(model, f)
    return out_path, {"n": len(y), "pos_rate": float(y.mean())}
