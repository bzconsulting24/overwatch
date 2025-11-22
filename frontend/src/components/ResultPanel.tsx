import { AnalysisResult, AnalysisStatus } from "../types";

type Props = {
  result: AnalysisResult | null;
  status: AnalysisStatus;
};

const Section = ({ title, items }: { title: string; items: string[] }) => (
  <div className="result-card">
    <h3>{title}</h3>
    <ul>
      {items.length === 0 && <li className="muted">No data</li>}
      {items.map((item, idx) => (
        <li key={idx}>{item}</li>
      ))}
    </ul>
  </div>
);

export function ResultPanel({ result, status }: Props) {
  const emptyState = status === "running" ? "Crunching..." : "No run yet.";

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Results</p>
          <h2>Transcript + Signals</h2>
        </div>
      </div>

      {!result && <p className="muted">{emptyState}</p>}

      {result && (
        <div className="result-grid">
          <div className="result-card full">
            <h3>Transcript</h3>
            <pre className="transcript">{result.transcript}</pre>
          </div>

          <Section title="Cheating Indicators" items={result.cheatingIndicators} />
          <Section title="Keyboard Sounds" items={result.keyboardFindings} />
          <Section title="Behavior Summary" items={result.behaviorSummary} />
          <Section title="OpenFace Insights" items={result.openfaceInsights} />

          {result.log && (
            <div className="result-card full">
              <h3>Pipeline log</h3>
              <ul>
                {result.log.map((line, idx) => (
                  <li key={idx}>{line}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
