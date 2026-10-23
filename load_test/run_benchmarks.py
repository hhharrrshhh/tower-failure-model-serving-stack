"""
Automated Load Testing & Benchmarking Runner
Task 6 Implementation:
Runs headless Locust scenarios against the prediction service at 10, 100, and 500 concurrency,
parses measured statistics, and produces reproducible evidence tables.
"""

import os
import sys
import time
import subprocess
import json
import pandas as pd

RESULTS_DIR = os.path.join("load_test", "results")
TARGET_HOST = os.environ.get("TARGET_HOST", "http://127.0.0.1:8000")

SCENARIOS = [
    {"name": "Low_Concurrency", "users": 10, "spawn_rate": 5, "duration": "20s"},
    {"name": "Medium_Concurrency", "users": 100, "spawn_rate": 20, "duration": "25s"},
    {"name": "Peak_Stress_500", "users": 500, "spawn_rate": 50, "duration": "30s"},
]

def run_scenario(scenario: dict, prefix="run"):
    name = f"{prefix}_{scenario['name']}"
    users = scenario["users"]
    spawn = scenario["spawn_rate"]
    duration = scenario["duration"]
    csv_prefix = os.path.join(RESULTS_DIR, name)

    print(f"\n[+] Executing Scenario: {name} (Users: {users}, Spawn: {spawn}/s, Duration: {duration}) -> {TARGET_HOST}")

    cmd = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        os.path.join("load_test", "locustfile.py"),
        "--headless",
        "-H",
        TARGET_HOST,
        "-u",
        str(users),
        "-r",
        str(spawn),
        "--run-time",
        duration,
        "--csv",
        csv_prefix,
        "--csv-full-history",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Warning: Locust exited with code {result.returncode}")

    # Parse output stats CSV
    stats_file = f"{csv_prefix}_stats.csv"
    if os.path.exists(stats_file):
        df_stats = pd.read_csv(stats_file)
        agg_row = df_stats[df_stats["Name"] == "Aggregated"]
        if not agg_row.empty:
            row = agg_row.iloc[0]
            req_count = int(row["Request Count"])
            fail_count = int(row["Failure Count"])
            error_rate = (fail_count / req_count * 100) if req_count > 0 else 0.0
            rps = float(row["Requests/s"])
            med_lat = float(row["50%"])
            p95_lat = float(row["95%"])
            p99_lat = float(row["99%"])
            max_lat = float(row["Max Response Time"])

            record = {
                "scenario": scenario["name"],
                "concurrency": users,
                "requests": req_count,
                "failures": fail_count,
                "error_rate_pct": round(error_rate, 2),
                "throughput_rps": round(rps, 2),
                "p50_ms": round(med_lat, 2),
                "p95_ms": round(p95_lat, 2),
                "p99_ms": round(p99_lat, 2),
                "max_ms": round(max_lat, 2),
            }
            return record

    print(f"[!] Could not locate stats file {stats_file}")
    return None

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stage = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    records = []

    print(f"=== Starting Load Test Suite (Stage: {stage}) ===")
    for sc in SCENARIOS:
        rec = run_scenario(sc, prefix=stage)
        if rec:
            records.append(rec)
        time.sleep(3)

    summary_file = os.path.join(RESULTS_DIR, f"{stage}_summary.json")
    with open(summary_file, "w") as f:
        json.dump(records, f, indent=2)

    print("\n==================== MEASURED RESULTS TABLE ====================")
    df_res = pd.DataFrame(records)
    print(df_res.to_string(index=False))
    print("================================================================")
    print(f"[SUCCESS] Results saved to {summary_file}")

if __name__ == "__main__":
    main()
