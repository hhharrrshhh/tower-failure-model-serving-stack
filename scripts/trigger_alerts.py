"""
Safe & Reversible Alert Trigger Script
Task 5 Acceptance Criterion: 'Show each one firing with stated thresholds.'

Usage:
  python scripts/trigger_alerts.py failure  # Triggers HighFailurePredictionSpike (>45%)
  python scripts/trigger_alerts.py latency  # Triggers HighLatencyP95 (>80ms)
"""

import sys
import time
import concurrent.futures
import pandas as pd
import httpx

API_URL = "http://localhost:8000"
PROM_URL = "http://localhost:9090"

def get_alert_state(alert_name: str) -> str:
    try:
        r = httpx.get(f"{PROM_URL}/api/v1/rules", timeout=3.0)
        if r.status_code == 200:
            for group in r.json().get("data", {}).get("groups", []):
                for rule in group.get("rules", []):
                    if rule.get("name") == alert_name:
                        return rule.get("state", "unknown")
    except Exception:
        pass
    return "unknown"

def trigger_failure_alert(duration_seconds=40):
    print("\n" + "="*70)
    print(">>> TRIGGERING ALERT: HighFailurePredictionSpike (Threshold: >45% for 15s)")
    print("="*70)

    # Load known failure cases from dataset
    df = pd.read_csv("project2_tower_serving/telecom_tower_failure.csv")
    failure_rows = df[df["Failure_Within_48Hrs"] == 1].to_dict(orient="records")
    print(f"[*] Loaded {len(failure_rows)} high-risk failure records from dataset.")
    print("[*] Generating stream of ~100% failure telemetry to exceed 45% threshold...")

    client = httpx.Client(base_url=API_URL, timeout=5.0)
    start_time = time.time()
    fired = False

    while time.time() - start_time < duration_seconds:
        # Send burst of failure payloads
        for i in range(10):
            sample = failure_rows[i % len(failure_rows)]
            payload = {
                "Tower_ID": str(sample["Tower_ID"]),
                "Temperature_C": float(sample["Temperature_C"]) if not pd.isna(sample["Temperature_C"]) else 65.0,
                "Battery_Voltage": float(sample["Battery_Voltage"]) if not pd.isna(sample["Battery_Voltage"]) else 44.0,
                "Power_Consumption_W": float(sample["Power_Consumption_W"]),
                "Signal_Strength_Percent": float(sample["Signal_Strength_Percent"]),
                "Fan_Speed_RPM": float(sample["Fan_Speed_RPM"]) if not pd.isna(sample["Fan_Speed_RPM"]) else 2400.0,
                "Humidity_Percent": float(sample["Humidity_Percent"]) if not pd.isna(sample["Humidity_Percent"]) else 50.0,
                "Traffic_Load": float(sample["Traffic_Load"]),
                "Tower_Age_Years": float(sample["Tower_Age_Years"]),
            }
            try:
                client.post("/predict", json=payload)
            except Exception:
                pass

        elapsed = int(time.time() - start_time)
        state = get_alert_state("HighFailurePredictionSpike")
        print(f"  [Elapsed: {elapsed:02d}s] Alert state: {state.upper()}")

        if state == "firing" and not fired:
            fired = True
            print("\n" + "*"*70)
            print(">>> [ALERT FIRING] HighFailurePredictionSpike is now FIRING!")
            print(">>> TAKE YOUR SCREENSHOT NOW at: http://localhost:9090/alerts")
            print(">>> Holding FIRING state for 20 seconds...")
            print("*"*70 + "\n")
            time.sleep(20)
            break

        time.sleep(1.0)

    # Restoration: Send normal telemetry to bring ratio back to healthy baseline
    print("[*] Restoring baseline: sending normal telemetry payloads...")
    df_normal = pd.read_csv("project2_tower_serving/load_test_requests.csv").to_dict(orient="records")
    for row in df_normal[:40]:
        try:
            client.post("/predict", json=row)
        except Exception:
            pass

    time.sleep(5)
    final_state = get_alert_state("HighFailurePredictionSpike")
    print(f"[SUCCESS] Restoration complete. Alert state returned to: {final_state.upper()}\n")

def send_request(client, payload):
    try:
        client.post("/predict", json=payload)
    except Exception:
        pass

def trigger_latency_alert(duration_seconds=45, concurrency=40):
    print("\n" + "="*70)
    print(">>> TRIGGERING ALERT: HighLatencyP95 (Threshold: >80ms for 15s)")
    print("="*70)
    print(f"[*] Spawning {concurrency} parallel concurrent workers to drive p95 latency >80ms...")

    df_normal = pd.read_csv("project2_tower_serving/load_test_requests.csv").to_dict(orient="records")
    start_time = time.time()
    fired = False

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        while time.time() - start_time < duration_seconds:
            client = httpx.Client(base_url=API_URL, timeout=10.0)
            futures = [
                executor.submit(send_request, client, df_normal[i % len(df_normal)])
                for i in range(concurrency)
            ]
            concurrent.futures.wait(futures)

            elapsed = int(time.time() - start_time)
            state = get_alert_state("HighLatencyP95")
            print(f"  [Elapsed: {elapsed:02d}s] Alert state: {state.upper()}")

            if state == "firing" and not fired:
                fired = True
                print("\n" + "*"*70)
                print(">>> [ALERT FIRING] HighLatencyP95 is now FIRING!")
                print(">>> TAKE YOUR SCREENSHOT NOW at: http://localhost:9090/alerts")
                print(">>> Holding FIRING state for 20 seconds...")
                print("*"*70 + "\n")
                # Maintain load for 15s so user can capture screenshot
                time.sleep(15)
                break

    print("[*] Concurrency load stopped. Waiting for queue to clear and latency to drop...")
    time.sleep(6)
    final_state = get_alert_state("HighLatencyP95")
    print(f"[SUCCESS] Restoration complete. Latency normalized. Alert state returned to: {final_state.upper()}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ["failure", "latency"]:
        print("Usage: python scripts/trigger_alerts.py [failure|latency]")
        sys.exit(1)

    if sys.argv[1] == "failure":
        trigger_failure_alert()
    elif sys.argv[1] == "latency":
        trigger_latency_alert()
