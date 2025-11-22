import { InputPanel } from "./components/InputPanel";
import { ProgressPanel } from "./components/ProgressPanel";
import { ResultPanel } from "./components/ResultPanel";
import { useAnalysisClient } from "./hooks/useAnalysisClient";

function App() {
  const { startAnalysis, status, progress, result, error, reset } = useAnalysisClient();

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Overwatch</p>
          <h1>
            React + TypeScript front-end for the Python analysis engine
            <span className="accent-dot">.</span>
          </h1>
          <p className="lede">
            Paste a video URL, let the Python pipeline handle transcription, diarization,
            keyboard sound checks, and OpenFace insights. Designed for clarity and fast review.
          </p>
          <div className="chips">
            <span className="chip">Python backend</span>
            <span className="chip">REST-friendly</span>
            <span className="chip">Realtime progress</span>
          </div>
        </div>
      </header>

      <main className="grid">
        <section className="col">
          <InputPanel onSubmit={startAnalysis} disabled={status === "running"} />
          <ProgressPanel status={status} progress={progress} error={error} onReset={reset} />
        </section>
        <section className="col">
          <ResultPanel result={result} status={status} />
        </section>
      </main>
    </div>
  );
}

export default App;
