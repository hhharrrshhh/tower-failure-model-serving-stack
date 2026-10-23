# Raw Input Contract: Tower Failure Prediction Service

**Document Version:** 1.0.0  
**Associated Model:** `artifacts/model_v1.joblib`  
**Prediction Target:** `Failure_Within_48Hrs` (0 = Healthy, 1 = Predicted Failure within 48h)

---

## 1. Schema Specification

The service accepts raw telecom mobile tower telemetry readings. The raw fields must strictly adhere to the types and operational ranges below.

| Field Name | Data Type | Nullable | Plausible Range | Typical Operational Value | Units / Description |
|---|---|---|---|---|---|
| `Tower_ID` | `string` | No | Regex: `^TWR-[0-9]{5}$` | `TWR-00001` | Unique mobile tower identifier |
| `Temperature_C` | `float` | Yes | `[-40.0, 300.0]` | `48.0` | Cabinet internal temperature in °C. Readout >85°C indicates thermal emergency. |
| `Battery_Voltage` | `float` | Yes | `[0.0, 120.0]` | `48.0` | DC backup battery bank voltage in Volts. Nominal is 48V. |
| `Power_Consumption_W`| `float` / `int` | No | `[100.0, 3000.0]` | `860.0` | Total electrical draw in Watts across radios, baseband, and cooling. |
| `Signal_Strength_Percent`| `float` | No | `[0.0, 100.0]` | `80.0` | Antenna radiated power / signal coverage quality (0 to 100%). |
| `Fan_Speed_RPM` | `float` / `int` | Yes | `[0.0, 6000.0]` | `2900.0` | Cooling fan tachometer speed in RPM. 0 indicates fan stoppage failure. |
| `Humidity_Percent` | `float` | Yes | `[0.0, 100.0]` | `55.0` | Relative humidity percentage within equipment enclosure. |
| `Traffic_Load` | `float` | No | `[0.0, 1500.0]` | `460.0` | Current active subscriber erlangs / concurrent voice & data sessions. |
| `Tower_Age_Years` | `float` / `int` | No | `[0.0, 30.0]` | `8.0` | Operational duration of the physical site installation in years. |

---

## 2. Validation & Edge-Case Handling

1. **Missing Values**:
   - The fields `Temperature_C`, `Battery_Voltage`, `Fan_Speed_RPM`, and `Humidity_Percent` may be omitted or sent as `null` if a sensor has intermittent telemetry failure.
   - When received as `null`, the single reusable preprocessing module (`TowerFeatureEngineer`) automatically imputes the median value calculated from historical production baselines without crashing.
2. **Out-of-Bounds Rejection**:
   - Readings outside the defined physical bounds (e.g., negative fan speeds, humidity >100%, battery voltage >72V, temperature <-40°C) are strictly rejected with HTTP `422 Unprocessable Entity` and a descriptive validation error message.
3. **Identifier Ignored for Inference**:
   - `Tower_ID` is mandatory for tracking and traceability in the prediction response, but is dropped before feature tensor generation.

---

## 3. Example Valid Payloads

### Single Tower Request
```json
{
  "Tower_ID": "TWR-09001",
  "Temperature_C": 49.5,
  "Battery_Voltage": 48.2,
  "Power_Consumption_W": 870,
  "Signal_Strength_Percent": 78.4,
  "Fan_Speed_RPM": 2950,
  "Humidity_Percent": 54.0,
  "Traffic_Load": 182.4,
  "Tower_Age_Years": 4
}
```

### Batch Prediction Request
```json
{
  "readings": [
    {
      "Tower_ID": "TWR-09001",
      "Temperature_C": 49.5,
      "Battery_Voltage": 48.2,
      "Power_Consumption_W": 870,
      "Signal_Strength_Percent": 78.4,
      "Fan_Speed_RPM": 2950,
      "Humidity_Percent": 54.0,
      "Traffic_Load": 182.4,
      "Tower_Age_Years": 4
    },
    {
      "Tower_ID": "TWR-09002",
      "Temperature_C": 51.5,
      "Battery_Voltage": 47.9,
      "Power_Consumption_W": 910,
      "Signal_Strength_Percent": 82.1,
      "Fan_Speed_RPM": 2800,
      "Humidity_Percent": 52.0,
      "Traffic_Load": 286.7,
      "Tower_Age_Years": 1
    }
  ]
}
```
