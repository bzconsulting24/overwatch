import { AnalysisStatus } from "../types";

type Props = {
  status: AnalysisStatus;
  progress: number;
  error?: string | null;
  onReset: () => void;
};

const statusCopy: Record<AnalysisStatus, string> = {
  idle: "Waiting to start",
  running: "Processing...",
  completed: "Done",
  error: "Error"
};

export function ProgressPanel({ status, progress, error, onReset }: Props) {
  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Progress</p>
          <h2>{statusCopy[status]}</h2>
        </div>
        <button className="ghost" onClick={onReset}>
          Reset
        </button>
      </div>

      <div className="progress-shell">
        <div className="progress-bar" style={{ width: `${progress}%` }} />
      </div>
      <p className="meta">{progress}%</p>
      {error && <p className="error">Error: {error}</p>}

      <ul className="checklist">
        <li className={progress >= 10 ? "done" : ""}>Download + audio extraction</li>
        <li className={progress >= 35 ? "done" : ""}>Speech + diarization</li>
        <li className={progress >= 60 ? "done" : ""}>OpenFace behavior sweep</li>
        <li className={progress >= 80 ? "done" : ""}>Flag sensitive words + keyboard</li>
        <li className={progress >= 100 ? "done" : ""}>Compile transcript + insights</li>
      </ul>
    </div>
  );
}
