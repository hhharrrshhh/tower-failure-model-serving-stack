"""
Pydantic schemas for the Tower Failure Prediction Service.
Implements strict validation and bounds-checking per docs/input_contract.md.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class TowerReading(BaseModel):
    Tower_ID: str = Field(..., description="Unique mobile tower identifier", pattern=r"^TWR-[0-9A-Za-z]+$")
    Temperature_C: Optional[float] = Field(None, ge=-40.0, le=300.0, description="Cabinet temperature in °C")
    Battery_Voltage: Optional[float] = Field(None, ge=0.0, le=120.0, description="Backup battery bank voltage in V")
    Power_Consumption_W: float = Field(..., ge=100.0, le=3000.0, description="Power drawn in Watts")
    Signal_Strength_Percent: float = Field(..., ge=0.0, le=100.0, description="Signal strength percentage")
    Fan_Speed_RPM: Optional[float] = Field(None, ge=0.0, le=6000.0, description="Cooling fan speed in RPM")
    Humidity_Percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity percentage")
    Traffic_Load: float = Field(..., ge=0.0, le=1500.0, description="Network traffic load")
    Tower_Age_Years: float = Field(..., ge=0.0, le=30.0, description="Physical site age in years")

class BatchPredictionRequest(BaseModel):
    readings: List[TowerReading] = Field(..., min_length=1, description="List of tower sensor readings")

class PredictionResult(BaseModel):
    Tower_ID: str
    prediction: int = Field(..., description="0 = Healthy, 1 = Predicted Failure within 48h")
    failure_probability: float = Field(..., description="Estimated probability of failure")
    risk_level: str = Field(..., description="'LOW' or 'HIGH'")

class PredictionResponse(BaseModel):
    model_version: str
    predictions: List[PredictionResult]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str

class VersionResponse(BaseModel):
    model_version: str
    created_at: str
    algorithm: str
