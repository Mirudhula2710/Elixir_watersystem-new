import json
import joblib
import os
import pandas as pd
import logging

try:
    import sklearn
except Exception as e:
    sklearn = None
    logging.warning(f"sklearn import failed: {e}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, 'model_artifacts')

_model = None
_metadata = None

def load_model():
    global _model, _metadata
    if sklearn is None:
        _model = None
        return
    try:
        with open(os.path.join(ARTIFACTS_DIR, 'model_metadata.json'), 'r') as f:
            _metadata = json.load(f)
            
        model_version = _metadata.get('sklearn_version')
        if model_version and hasattr(sklearn, '__version__') and model_version != sklearn.__version__:
            logging.warning(f"WARNING: scikit-learn version mismatch! Model was trained with {model_version}, current is {sklearn.__version__}.")
            
        _model = joblib.load(os.path.join(ARTIFACTS_DIR, 'severity_model.pkl'))
    except Exception as e:
        logging.warning(f"WARNING: Failed to load ML model from disk. {type(e).__name__}: {e}")
        _model = None

load_model()

def predict_severity(feature_dict):
    """
    Given a dictionary of features, runs it through the pre-trained ML model.
    If the model is unavailable, returns 'Normal' (fallback physics handles true severity).
    """
    if _model is None:
        logging.warning("WARNING: ML Model is unavailable. Falling back to physics-only detection.")
        return "Normal"

    try:
        # Create a single-row DataFrame from the feature dict to feed the pipeline
        base_features = _metadata.get('base_features', ['hour', 'minute_of_day', 'tank_level', 'expected_level', 'rate_of_change', 'zone'])
        
        # We need the 'zone' categorical variable since the Pipeline expects it
        zone_val = 'Unknown'
        for k, v in feature_dict.items():
            if k.startswith('zone_') and v == 1:
                zone_val = k.replace('zone_', '')
                break
                
        # Reconstruct base features dict
        df_dict = {
            'hour': [feature_dict.get('hour', 0)],
            'minute_of_day': [feature_dict.get('minute_of_day', 0)],
            'tank_level': [feature_dict.get('tank_level', 0.0)],
            'expected_level': [feature_dict.get('expected_level', 0.0)],
            'rate_of_change': [feature_dict.get('rate_of_change', 0.0)],
            'zone': [zone_val]
        }
        df = pd.DataFrame(df_dict)
        
        pred = _model.predict(df)[0]
        return pred
    except Exception as e:
        logging.error(f"ML Predict error: {e}")
        return "Normal"
