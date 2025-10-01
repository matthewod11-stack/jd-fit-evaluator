
import json, pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

FEATURE_KEYS = ["title","industry","skills","context","tenure","recency","bonus"]

def load_features(scores_path: str, labels_path: str):
    rows = json.loads(Path(scores_path).read_text())
    # Build X from subscores in scores.json
    feats = {}
    for r in rows:
        name = r.get("candidate") or r.get("name") or ""
        subs = {k: r.get(k, None) for k in FEATURE_KEYS}
        # fallback if subs nested
        if subs["title"] is None and "why" in r and "subs" in r:
            subs = r["subs"]
        x = [float(subs.get(k, 0.0)) for k in FEATURE_KEYS]
        feats[name] = np.array(x, dtype="float32")
    # Load labels CSV name,label or candidate_id,label
    ymap = {}
    for line in Path(labels_path).read_text().splitlines():
        line=line.strip()
        if not line or line.lower().startswith("name"): 
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2: 
            continue
        ymap[parts[0]] = int(parts[1])
    # Align
    X, y, names = [], [], []
    for n, x in feats.items():
        if n in ymap:
            X.append(x); y.append(ymap[n]); names.append(n)
    if not X:
        raise ValueError("No overlapping candidates between features and labels.")
    X = np.vstack(X); y = np.array(y, dtype="int64")
    return X, y, names

def train(scores_path: str = "data/out/scores.json", labels_csv: str = "data/labels.csv", out_path: str = "models/trained/model.pkl"):
    scores = pd.read_json(scores_path)
    labels = pd.read_csv(labels_csv)
    if "candidate_id" not in scores.columns or "candidate_id" not in labels.columns:
        raise SystemExit("labels and scores must contain candidate_id")
    df = scores.merge(labels[["candidate_id","label"]], on="candidate_id", how="inner")
    
    # Build X from the merged dataframe
    X, y, names = [], [], []
    for _, row in df.iterrows():
        # Extract features using FEATURE_KEYS
        subs = {k: row.get(k, None) for k in FEATURE_KEYS}
        # fallback if subs nested in a 'subs' column
        if subs["title"] is None and "subs" in row:
            subs = row["subs"] if isinstance(row["subs"], dict) else {}
        x = [float(subs.get(k, 0.0) or 0.0) for k in FEATURE_KEYS]
        X.append(np.array(x, dtype="float32"))
        y.append(int(row["label"]))
        names.append(row.get("candidate_id", ""))
    
    if not X:
        raise ValueError("No overlapping candidates between features and labels.")
    
    X = np.vstack(X)
    y = np.array(y, dtype="int64")
    
    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    clf.fit(X, y)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump(clf, f)
    return out_path, {"n": len(y), "pos_rate": float(y.mean())}
