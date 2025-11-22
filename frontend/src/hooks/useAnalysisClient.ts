import { useEffect, useMemo, useRef, useState } from "react";
import { AnalysisPayload, AnalysisResult, AnalysisStatus } from "../types";

type UseAnalysisClient = {
  status: AnalysisStatus;
  progress: number;
  result: AnalysisResult | null;
  error: string | null;
  startAnalysis: (payload: AnalysisPayload) => Promise<void>;
  reset: () => void;
};

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || "";

export function useAnalysisClient(): UseAnalysisClient {
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const stopRef = useRef(false);

  const clearTimer = () => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => clearTimer, []);

  const pollJob = (jobId: string) =>
    new Promise<void>((resolve, reject) => {
      stopRef.current = false;
      timerRef.current = window.setInterval(async () => {
        if (stopRef.current) return;
        try {
          const res = await fetch(`${API_BASE}/api/analyze/${jobId}`);
          if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
          const data = await res.json();
          setProgress(data.progress ?? 0);

          if (data.status === "error") {
            stopRef.current = true;
            clearTimer();
            setStatus("error");
            setError(data.error || "Job failed");
            return reject(new Error(data.error || "Job failed"));
          }

          if (data.status === "completed") {
            stopRef.current = true;
            clearTimer();
            setStatus("completed");
            setProgress(100);
            if (data.result) {
              setResult({
                transcript: data.result.transcript ?? "",
                cheatingIndicators: data.result.cheatingIndicators ?? [],
                keyboardFindings: data.result.keyboardFindings ?? [],
                behaviorSummary: data.result.behaviorSummary ?? [],
                openfaceInsights: data.result.openfaceInsights ?? [],
                log: data.result.log ?? []
              });
            }
            return resolve();
          }

          setStatus("running");
        } catch (err) {
          stopRef.current = true;
          clearTimer();
          setStatus("error");
          setError(err instanceof Error ? err.message : "Polling error");
          return reject(err);
        }
      }, 900);
    });

  const startAnalysis = async (payload: AnalysisPayload) => {
    try {
      setError(null);
      setResult(null);
      setStatus("running");
      setProgress(5);
      stopRef.current = false;

      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const message = `Failed to start analysis: ${res.status}`;
        setStatus("error");
        setError(message);
        return;
      }
      const { jobId } = await res.json();
      if (!jobId) {
        const message = "Missing jobId from backend";
        setStatus("error");
        setError(message);
        return;
      }
      await pollJob(jobId);
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  const reset = () => {
    clearTimer();
    stopRef.current = true;
    setStatus("idle");
    setProgress(0);
    setResult(null);
    setError(null);
  };

  return useMemo(
    () => ({
      status,
      progress,
      result,
      error,
      startAnalysis,
      reset
    }),
    [status, progress, result, error, startAnalysis, reset]
  );
}
