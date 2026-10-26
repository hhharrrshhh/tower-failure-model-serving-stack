import { useState, FormEvent } from "react";
import { RotateCcw, Zap, FlaskConical, Loader2 } from "lucide-react";
import { TowerReading } from "../api";

// ── Field definitions ────────────────────────────────────────────────────────

interface FieldDef {
  key: keyof Omit<TowerReading, "Tower_ID">;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  required: boolean;
  placeholder: string;
}

const FIELDS: FieldDef[] = [
  { key: "Temperature_C",         label: "Temperature",          unit: "°C",  min: -40,  max: 300,  step: 0.1,  required: false, placeholder: "e.g. 35.0" },
  { key: "Battery_Voltage",       label: "Battery Voltage",      unit: "V",   min: 0,    max: 120,  step: 0.1,  required: false, placeholder: "e.g. 48.0" },
  { key: "Power_Consumption_W",   label: "Power Consumption",    unit: "W",   min: 100,  max: 3000, step: 1,    required: true,  placeholder: "e.g. 800" },
  { key: "Signal_Strength_Percent",label:"Signal Strength",      unit: "%",   min: 0,    max: 100,  step: 0.1,  required: true,  placeholder: "e.g. 75.0" },
  { key: "Fan_Speed_RPM",         label: "Fan Speed",            unit: "RPM", min: 0,    max: 6000, step: 1,    required: false, placeholder: "e.g. 1200" },
  { key: "Humidity_Percent",      label: "Humidity",             unit: "%",   min: 0,    max: 100,  step: 0.1,  required: false, placeholder: "e.g. 60.0" },
  { key: "Traffic_Load",          label: "Traffic Load",         unit: "",    min: 0,    max: 1500, step: 1,    required: true,  placeholder: "e.g. 450" },
  { key: "Tower_Age_Years",       label: "Tower Age",            unit: "yrs", min: 0,    max: 30,   step: 0.5,  required: true,  placeholder: "e.g. 5.0" },
];

const EXAMPLE: Record<string, string> = {
  Tower_ID: "TWR-DEMO01",
  Temperature_C: "42.5",
  Battery_Voltage: "46.8",
  Power_Consumption_W: "950",
  Signal_Strength_Percent: "62.0",
  Fan_Speed_RPM: "1800",
  Humidity_Percent: "71.0",
  Traffic_Load: "520",
  Tower_Age_Years: "8",
};

const BLANK: Record<string, string> = Object.fromEntries(
  ["Tower_ID", ...FIELDS.map((f) => f.key)].map((k) => [k, ""])
);

// ── Component ────────────────────────────────────────────────────────────────

interface Props {
  onSubmit: (reading: TowerReading) => void;
  loading: boolean;
  disabled: boolean;
}

export default function PredictForm({ onSubmit, loading, disabled }: Props) {
  const [values, setValues] = useState<Record<string, string>>(BLANK);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const set = (key: string, val: string) => {
    setValues((v) => ({ ...v, [key]: val }));
    if (errors[key]) setErrors((e) => { const n = { ...e }; delete n[key]; return n; });
  };

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!values.Tower_ID.trim()) errs.Tower_ID = "Required";
    else if (!/^TWR-[0-9A-Za-z]+$/.test(values.Tower_ID.trim()))
      errs.Tower_ID = "Format: TWR-<alphanumeric>";

    for (const f of FIELDS) {
      const raw = values[f.key];
      if (f.required && raw.trim() === "") { errs[f.key] = "Required"; continue; }
      if (raw.trim() !== "") {
        const n = parseFloat(raw);
        if (isNaN(n)) { errs[f.key] = "Must be a number"; continue; }
        if (n < f.min || n > f.max) errs[f.key] = `Range: ${f.min}–${f.max}`;
      }
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    const reading: TowerReading = {
      Tower_ID: values.Tower_ID.trim(),
      Power_Consumption_W: parseFloat(values.Power_Consumption_W),
      Signal_Strength_Percent: parseFloat(values.Signal_Strength_Percent),
      Traffic_Load: parseFloat(values.Traffic_Load),
      Tower_Age_Years: parseFloat(values.Tower_Age_Years),
    };
    if (values.Temperature_C.trim())  reading.Temperature_C  = parseFloat(values.Temperature_C);
    if (values.Battery_Voltage.trim()) reading.Battery_Voltage = parseFloat(values.Battery_Voltage);
    if (values.Fan_Speed_RPM.trim())   reading.Fan_Speed_RPM   = parseFloat(values.Fan_Speed_RPM);
    if (values.Humidity_Percent.trim()) reading.Humidity_Percent = parseFloat(values.Humidity_Percent);
    onSubmit(reading);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white border border-gray-200 rounded-xl p-5 space-y-5"
      noValidate
    >
      {/* Tower ID — full width */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Tower ID <span className="text-red-400">*</span>
        </label>
        <input
          id="tower-id"
          type="text"
          value={values.Tower_ID}
          onChange={(e) => set("Tower_ID", e.target.value)}
          placeholder="e.g. TWR-A001"
          className={`w-full border rounded-lg px-3 py-2 text-sm font-mono placeholder-gray-300 outline-none transition
            focus:ring-1 focus:ring-blue-400 focus:border-blue-400
            ${errors.Tower_ID ? "border-red-300 bg-red-50" : "border-gray-200 bg-gray-50 hover:border-gray-300"}`}
        />
        {errors.Tower_ID && <p className="text-xs text-red-500 mt-1">{errors.Tower_ID}</p>}
      </div>

      {/* 2-column sensor grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {FIELDS.map((f) => (
          <div key={f.key}>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              {f.label}
              {f.unit && <span className="text-gray-400 font-normal ml-1">({f.unit})</span>}
              {f.required ? <span className="text-red-400 ml-1">*</span> : <span className="text-gray-300 ml-1 text-xs">optional</span>}
            </label>
            <input
              id={`field-${f.key}`}
              type="number"
              step={f.step}
              min={f.min}
              max={f.max}
              value={values[f.key]}
              onChange={(e) => set(f.key, e.target.value)}
              placeholder={f.placeholder}
              className={`w-full border rounded-lg px-3 py-2 text-sm placeholder-gray-300 outline-none transition
                focus:ring-1 focus:ring-blue-400 focus:border-blue-400
                ${errors[f.key] ? "border-red-300 bg-red-50" : "border-gray-200 bg-gray-50 hover:border-gray-300"}`}
            />
            {errors[f.key] && <p className="text-xs text-red-500 mt-1">{errors[f.key]}</p>}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button
          id="btn-predict"
          type="submit"
          disabled={loading || disabled}
          className="flex items-center gap-1.5 bg-gray-900 text-white text-sm font-medium px-4 py-2 rounded-lg
            hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading
            ? <><Loader2 size={14} className="animate-spin" /> Running…</>
            : <><Zap size={14} /> Predict Failure Risk</>}
        </button>
        <button
          id="btn-example"
          type="button"
          onClick={() => { setValues(EXAMPLE); setErrors({}); }}
          disabled={loading}
          className="flex items-center gap-1.5 border border-gray-200 text-gray-600 text-sm px-3 py-2 rounded-lg
            hover:border-gray-300 hover:bg-gray-50 disabled:opacity-40 transition-colors"
        >
          <FlaskConical size={14} /> Load Example
        </button>
        <button
          id="btn-reset"
          type="button"
          onClick={() => { setValues(BLANK); setErrors({}); }}
          disabled={loading}
          className="flex items-center gap-1.5 text-gray-400 text-sm px-3 py-2 rounded-lg
            hover:text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition-colors"
        >
          <RotateCcw size={14} /> Reset
        </button>
      </div>
    </form>
  );
}
