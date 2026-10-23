"""
Tower Serving Stack - Reusable Feature Engineering Module
Shared between training (src/train.py) and serving (src/app.py).
"""

from typing import List, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

RAW_FEATURE_COLUMNS: List[str] = [
    "Temperature_C",
    "Battery_Voltage",
    "Power_Consumption_W",
    "Signal_Strength_Percent",
    "Fan_Speed_RPM",
    "Humidity_Percent",
    "Traffic_Load",
    "Tower_Age_Years",
]

class TowerFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Transforms raw telecom tower sensor readings into model features:
    1. Imputes missing sensor readings (median strategy)
    2. Generates domain interaction features:
       - temp_to_fan: ratio of cabinet temperature to cooling fan RPM
       - power_to_traffic: energy consumed per unit traffic load
       - stress_index: composite thermal-electrical stress index
    """

    def __init__(self):
        self.median_values_ = {}
        self.feature_names_out_ = []

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y=None):
        if not isinstance(X, pd.DataFrame):
            df = pd.DataFrame(X, columns=RAW_FEATURE_COLUMNS)
        else:
            df = X.copy()

        # Compute median imputation values for raw features
        for col in RAW_FEATURE_COLUMNS:
            self.median_values_[col] = float(df[col].median() if not pd.isna(df[col].median()) else 0.0)

        self.feature_names_out_ = RAW_FEATURE_COLUMNS + [
            "temp_to_fan",
            "power_to_traffic",
            "stress_index",
        ]
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            raw = X[RAW_FEATURE_COLUMNS].to_numpy(dtype=float, copy=True)
        else:
            raw = np.array(X, dtype=float, copy=True)

        # Impute missing values (columns 0, 1, 4, 5) using fitted medians
        for idx, col in enumerate(RAW_FEATURE_COLUMNS):
            median_val = self.median_values_.get(col, 0.0)
            nan_mask = np.isnan(raw[:, idx])
            if np.any(nan_mask):
                raw[nan_mask, idx] = median_val

        # Domain feature engineering using vector numpy operations
        temp = raw[:, 0]
        power = raw[:, 2]
        fan = raw[:, 4]
        traffic = raw[:, 6]

        temp_to_fan = temp / (fan + 1.0)
        power_to_traffic = power / (traffic + 1.0)
        stress_index = (temp * power) / (fan + 1.0)

        # Stack into final feature matrix (8 raw features + 3 engineered features)
        return np.column_stack([raw, temp_to_fan, power_to_traffic, stress_index])

    def get_feature_names_out(self, input_features=None):
        return np.array(self.feature_names_out_)
