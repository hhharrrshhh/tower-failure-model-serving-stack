// All API calls go through this base URL.
// In development: set VITE_API_BASE_URL in .env.local (e.g. http://localhost:8000)
// In production:  set VITE_API_BASE_URL in Vercel dashboard (e.g. https://your-app.onrender.com)
export const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  version: string;
}

export interface VersionResponse {
  model_version: string;
  created_at: string;
  algorithm: string;
}

export interface TowerReading {
  Tower_ID: string;
  Temperature_C?: number | null;
  Battery_Voltage?: number | null;
  Power_Consumption_W: number;
  Signal_Strength_Percent: number;
  Fan_Speed_RPM?: number | null;
  Humidity_Percent?: number | null;
  Traffic_Load: number;
  Tower_Age_Years: number;
}

export interface PredictionResult {
  Tower_ID: string;
  prediction: number;         // 0 = healthy, 1 = failure
  failure_probability: number;
  risk_level: "LOW" | "HIGH";
}

export interface PredictionResponse {
  model_version: string;
  predictions: PredictionResult[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(15000),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { message?: string }).message ?? `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: ()  => get<HealthResponse>("/health"),
  version: () => get<VersionResponse>("/version"),
  predict: (reading: TowerReading) =>
    post<PredictionResponse>("/predict", reading),
};
