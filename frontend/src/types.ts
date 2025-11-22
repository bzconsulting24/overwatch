export type AnalysisStatus = "idle" | "running" | "completed" | "error";

export interface AnalysisPayload {
  videoUrl: string;
  outputDir?: string;
  modelHint?: string;
}

export interface AnalysisResult {
  transcript: string;
  cheatingIndicators: string[];
  keyboardFindings: string[];
  behaviorSummary: string[];
  openfaceInsights: string[];
  log?: string[];
}
