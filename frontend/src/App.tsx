import { useEffect, useReducer, useCallback, useRef } from "react";
import {
  Activity, Server, Cpu, AlertTriangle, CheckCircle2,
  XCircle, Loader2, RefreshCw, ExternalLink, Clock,
} from "lucide-react";
import { api, TowerReading, PredictionResult, BASE } from "./api";
import PredictForm from "./components/PredictForm";

// ── Types ────────────────────────────────────────────────────────────────────

type ApiStatus = "checking" | "online" | "offline";

interface HistoryEntry extends PredictionResult {
  timestamp: string;
  model_version: string;
}

interface State {
  apiStatus: ApiStatus;
  modelLoaded: boolean;
  modelVersion: string;
  createdAt: string;
  predicting: boolean;
  predError: string | null;
  lastResult: PredictionResult | null;
  history: HistoryEntry[];
}

type Action =
  | { type: "STATUS_OK"; version: string; modelLoaded: boolean }
  | { type: "STATUS_ERR" }
  | { type: "VERSION_OK"; model_version: string; created_at: string }
  | { type: "PRED_START" }
  | { type: "PRED_OK"; result: PredictionResult; model_version: string }
  | { type: "PRED_ERR"; message: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "STATUS_OK":
      return { ...state, apiStatus: "online", modelLoaded: action.modelLoaded, modelVersion: action.version };
    case "STATUS_ERR":
      return { ...state, apiStatus: "offline", modelLoaded: false };
    case "VERSION_OK":
      return { ...state, modelVersion: action.model_version, createdAt: action.created_at };
    case "PRED_START":
      return { ...state, predicting: true, predError: null };
    case "PRED_OK": {
      const entry: HistoryEntry = {
        ...action.result,
        timestamp: new Date().toLocaleTimeString(),
        model_version: action.model_version,
      };
      return {
        ...state,
        predicting: false,
        lastResult: action.result,
        history: [entry, ...state.history].slice(0, 5),
      };
    }
    case "PRED_ERR":
      return { ...state, predicting: false, predError: action.message };
    default:
      return state;
  }
}

const INITIAL: State = {
  apiStatus: "checking",
  modelLoaded: false,
  modelVersion: "—",
  createdAt: "—",
  predicting: false,
  predError: null,
  lastResult: null,
  history: [],
};

// ── Small reusable atoms ─────────────────────────────────────────────────────

function StatusDot({ status }: { status: ApiStatus }) {
  const cfg = {
    checking: "bg-yellow-400",
    online:   "bg-green-400",
    offline:  "bg-red-400",
  } as const;
  return <span className={`inline-block w-2 h-2 rounded-full ${cfg[status]}`} />;
}

function RiskBadge({ level, prob }: { level: string; prob: number }) {
  const isHigh = level === "HIGH";
  const pct = Math.round(prob * 100);
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium
        ${isHigh ? "bg-red-50 text-red-700 border border-red-200" : "bg-green-50 text-green-700 border border-green-200"}`}
    >
      {isHigh ? <AlertTriangle size={11} /> : <CheckCircle2 size={11} />}
      {level} — {pct}%
    </span>
  );
}

// ── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [state, dispatch] = useReducer(reducer, INITIAL);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkStatus = useCallback(async () => {
    try {
      const [h, v] = await Promise.all([api.health(), api.version()]);
      dispatch({ type: "STATUS_OK", version: h.version, modelLoaded: h.model_loaded });
      dispatch({ type: "VERSION_OK", model_version: v.model_version, created_at: v.created_at });
    } catch {
      dispatch({ type: "STATUS_ERR" });
    }
  }, []);

  // Poll health every 30 s
  useEffect(() => {
    checkStatus();
    pollRef.current = setInterval(checkStatus, 30_000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [checkStatus]);

  const handlePredict = useCallback(async (reading: TowerReading) => {
    dispatch({ type: "PRED_START" });
    try {
      const res = await api.predict(reading);
      dispatch({ type: "PRED_OK", result: res.predictions[0], model_version: res.model_version });
    } catch (e) {
      dispatch({ type: "PRED_ERR", message: (e as Error).message });
    }
  }, []);

  const { apiStatus, modelLoaded, modelVersion, createdAt, predicting, predError, lastResult, history } = state;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Header ── */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gray-900 text-white rounded-lg p-1.5">
              <Activity size={18} />
            </div>
            <div>
              <h1 className="text-sm font-semibold leading-tight text-gray-900">Tower Failure Prediction</h1>
              <p className="text-xs text-gray-500 hidden sm:block">ML-powered telecom tower failure risk monitoring</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-xs text-gray-600">
              <StatusDot status={apiStatus} />
              <span className="font-medium">
                {apiStatus === "checking" ? "Checking…" : apiStatus === "online" ? "API Online" : "API Offline"}
              </span>
            </div>
            <div className="text-xs text-gray-400 hidden sm:block font-mono">{modelVersion}</div>
            <button
              onClick={checkStatus}
              title="Refresh status"
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* ── Offline banner ── */}
        {apiStatus === "offline" && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
            <XCircle size={16} className="shrink-0" />
            <span>Cannot reach the backend API. Check that the service is running and <code className="font-mono text-xs bg-red-100 px-1 rounded">VITE_API_BASE_URL</code> is set correctly.</span>
          </div>
        )}

        {/* ── Section A: System Status ── */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">System Status</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* API Health */}
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">API Health</span>
                <Server size={14} className="text-gray-300" />
              </div>
              <div className="flex items-center gap-2">
                <StatusDot status={apiStatus} />
                <span className="text-sm font-medium text-gray-800 capitalize">
                  {apiStatus === "checking" ? "Checking" : apiStatus}
                </span>
              </div>
            </div>
            {/* Model Status */}
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">Model Status</span>
                <Cpu size={14} className="text-gray-300" />
              </div>
              <div className="flex items-center gap-2">
                {apiStatus === "checking" ? (
                  <Loader2 size={12} className="animate-spin text-gray-400" />
                ) : modelLoaded ? (
                  <CheckCircle2 size={12} className="text-green-500" />
                ) : (
                  <XCircle size={12} className="text-red-400" />
                )}
                <span className="text-sm font-medium text-gray-800">
                  {apiStatus === "checking" ? "—" : modelLoaded ? "Loaded" : "Not loaded"}
                </span>
              </div>
            </div>
            {/* Model Version */}
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">Model Version</span>
                <Activity size={14} className="text-gray-300" />
              </div>
              <p className="text-sm font-medium font-mono text-gray-800">{modelVersion}</p>
              <p className="text-xs text-gray-400 mt-0.5 truncate">{createdAt}</p>
            </div>
          </div>
        </section>

        {/* ── Sections B+C: Form + Result ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Form — wider column */}
          <div className="lg:col-span-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Sensor Input</h2>
            <PredictForm onSubmit={handlePredict} loading={predicting} disabled={apiStatus === "offline"} />
          </div>

          {/* Result panel */}
          <div className="lg:col-span-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Prediction Result</h2>
            <ResultPanel result={lastResult} loading={predicting} error={predError} />
          </div>
        </div>

        {/* ── Section D: Recent History ── */}
        {history.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Recent Predictions</h2>
              <span className="text-xs text-gray-400">(session only)</span>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                    <th className="px-4 py-2.5 font-medium">Tower ID</th>
                    <th className="px-4 py-2.5 font-medium">Result</th>
                    <th className="px-4 py-2.5 font-medium">Probability</th>
                    <th className="px-4 py-2.5 font-medium hidden sm:table-cell">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {history.map((h, i) => (
                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-700">{h.Tower_ID}</td>
                      <td className="px-4 py-2.5">
                        <RiskBadge level={h.risk_level} prob={h.failure_probability} />
                      </td>
                      <td className="px-4 py-2.5 text-gray-600">{Math.round(h.failure_probability * 100)}%</td>
                      <td className="px-4 py-2.5 text-gray-400 text-xs hidden sm:table-cell">
                        <span className="flex items-center gap-1"><Clock size={10} />{h.timestamp}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ── Footer links ── */}
        <footer className="border-t border-gray-100 pt-6 flex flex-wrap gap-4 text-xs text-gray-400">
          <a href={`${BASE}/docs`}
            target="_blank" rel="noopener" className="flex items-center gap-1 hover:text-gray-600 transition-colors">
            <ExternalLink size={11} /> Swagger UI
          </a>
          <a href="http://localhost:9090" target="_blank" rel="noopener"
            className="flex items-center gap-1 hover:text-gray-600 transition-colors">
            <ExternalLink size={11} /> Prometheus
          </a>
          <a href="http://localhost:3000" target="_blank" rel="noopener"
            className="flex items-center gap-1 hover:text-gray-600 transition-colors">
            <ExternalLink size={11} /> Grafana
          </a>
          <span className="ml-auto">History resets on page reload. No data is stored client-side.</span>
        </footer>
      </main>
    </div>
  );
}

// ── Result Panel component ───────────────────────────────────────────────────

function ResultPanel({ result, loading, error }: {
  result: PredictionResult | null;
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 flex flex-col items-center justify-center gap-2 min-h-48 text-gray-400">
        <Loader2 size={22} className="animate-spin" />
        <p className="text-sm">Running inference…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 min-h-48 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-red-600 font-medium text-sm">
          <XCircle size={16} /> Prediction failed
        </div>
        <p className="text-xs text-red-500 break-words">{error}</p>
      </div>
    );
  }
  if (!result) {
    return (
      <div className="bg-white border border-gray-200 border-dashed rounded-xl p-6 flex flex-col items-center justify-center gap-2 min-h-48 text-gray-300">
        <Activity size={28} strokeWidth={1} />
        <p className="text-sm text-center">Fill in sensor values and click<br /><span className="font-medium text-gray-400">Predict Failure Risk</span></p>
      </div>
    );
  }

  const isFailure = result.prediction === 1;
  const pct = Math.round(result.failure_probability * 100);
  const barColor = isFailure ? "bg-red-400" : pct > 30 ? "bg-yellow-400" : "bg-green-400";

  return (
    <div className={`bg-white border rounded-xl p-6 min-h-48 flex flex-col gap-4
      ${isFailure ? "border-red-200" : "border-green-200"}`}>
      <div className="flex items-center gap-2">
        {isFailure
          ? <AlertTriangle size={18} className="text-red-500" />
          : <CheckCircle2 size={18} className="text-green-500" />}
        <span className={`text-sm font-semibold ${isFailure ? "text-red-700" : "text-green-700"}`}>
          {isFailure ? "Failure predicted" : "No failure predicted"}
        </span>
      </div>
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Failure probability</span>
          <span className="font-medium text-gray-700">{pct}%</span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="flex items-center justify-between mt-auto pt-3 border-t border-gray-100">
        <span className="text-xs text-gray-400">Risk level</span>
        <RiskBadge level={result.risk_level} prob={result.failure_probability} />
      </div>
      <div className="text-xs text-gray-400">
        Tower: <span className="font-mono text-gray-600">{result.Tower_ID}</span>
      </div>
    </div>
  );
}
