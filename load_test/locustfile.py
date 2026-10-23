"""
Locust Load Testing Suite for Tower Prediction Service
Task 6 Implementation: Replays realistic sensor payloads from load_test_requests.csv
across concurrency scenarios (10, 100, 500 users + spikes).
"""

import os
import random
import pandas as pd
from locust import HttpUser, task, between

DATA_PATH = os.path.join("project2_tower_serving", "load_test_requests.csv")

# Preload realistic payloads into memory once
if os.path.exists(DATA_PATH):
    _df = pd.read_csv(DATA_PATH)
    PAYLOADS = _df.to_dict(orient="records")
else:
    PAYLOADS = [
        {
            "Tower_ID": "TWR-09001",
            "Temperature_C": 49.5,
            "Battery_Voltage": 48.0,
            "Power_Consumption_W": 850.0,
            "Signal_Strength_Percent": 80.0,
            "Fan_Speed_RPM": 2900.0,
            "Humidity_Percent": 55.0,
            "Traffic_Load": 200.0,
            "Tower_Age_Years": 5.0,
        }
    ]

class TowerServingUser(HttpUser):
    # Think time between 10ms and 50ms to simulate fast telemetry agents
    wait_time = between(0.01, 0.05)

    @task(9)
    def predict_single_tower(self):
        """Main serving endpoint workload."""
        sample = random.choice(PAYLOADS)
        self.client.post("/predict", json=sample, name="/predict (Single)")

    @task(1)
    def check_health(self):
        """Simulate periodic health probe during traffic."""
        self.client.get("/health", name="/health")
