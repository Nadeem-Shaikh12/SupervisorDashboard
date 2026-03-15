"""
analytics/defect_predictor.py
==============================
Machine Learning module to predict defect probability.
Trains a model (e.g. LogisticRegression) on historical inspection data.
"""

import os
import logging
import pickle
from datetime import datetime
import numpy as np

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
except ImportError:
    pass # Assume installed during setup

from database.db import get_connection

logger = logging.getLogger("dreamvision.analytics.ml")

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "defect_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scaler.pkl")

# Cached model
_model = None
_scaler = None

def load_model():
    """Load pre-trained model on edge server startup."""
    global _model, _scaler
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                _model = pickle.load(f)
            with open(SCALER_PATH, "rb") as f:
                _scaler = pickle.load(f)
            logger.info("Defect Predictor Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
    else:
        logger.warning("No pre-trained model found. Run training script to enable predictions.")

def predict_defect_probability(component_name: str, temperature: float) -> float:
    """Predicts likelihood of defect."""
    global _model, _scaler
    if _model is None or _scaler is None:
        return 0.0

    # Basic feature engineering (using temperature + hour of day)
    hour = datetime.now().hour
    # Convert categorical to a simple hash or id. We'll simplify and use
    # string length for our mock logistic regression
    comp_id = len(component_name)

    X = np.array([[comp_id, temperature, hour]])
    X_scaled = _scaler.transform(X)

    # Predicting probability of class 1 (NOK/WARNING)
    try:
        prob = _model.predict_proba(X_scaled)[0][1]
        return float(prob)
    except IndexError:
        return 0.0

def train_model():
    """Data Science Pipeline to extract historical DB and fit a model."""
    logger.info("Extracting data for ML Training pipeline...")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT component_name, temperature, status, timestamp FROM parts_inspection")
        rows = cursor.fetchall()
        
    if len(rows) < 50:
        logger.warning(f"Not enough data to train model (found {len(rows)}, need 50).")
        return False

    X_train = []
    y_train = []

    for r in rows:
        comp_id = len(r['component_name'])
        temp = r['temperature']
        try:
            ts = datetime.fromisoformat(r['timestamp'])
            hour = ts.hour
        except:
            hour = 12
            
        is_defect = 1 if r['status'] in ['NOK', 'WARNING'] else 0
        
        X_train.append([comp_id, temp, hour])
        y_train.append(is_defect)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    
    # Class weight to handle imbalanced OK vs NOK
    model = LogisticRegression(class_weight='balanced')
    model.fit(X_scaled, y_train)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    logger.info("Data Science Pipeline complete. New Defect Prediction Model saved.")
    
    # Reload newly trained model into memory
    load_model()
    return True
