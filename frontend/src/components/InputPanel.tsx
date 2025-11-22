import { FormEvent, useState } from "react";
import { AnalysisPayload } from "../types";

type Props = {
  onSubmit: (payload: AnalysisPayload) => void;
  disabled?: boolean;
};

export function InputPanel({ onSubmit, disabled }: Props) {
  const [videoUrl, setVideoUrl] = useState("");
  const [outputDir, setOutputDir] = useState("./out");
  const [modelHint, setModelHint] = useState("default");

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!videoUrl) return;
    onSubmit({ videoUrl, outputDir, modelHint });
  };

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <div className="panel-head">
        <div>
          <p className="eyebrow">Input</p>
          <h2>Run an analysis</h2>
        </div>
        <button type="submit" className="primary" disabled={disabled || !videoUrl}>
          Start
        </button>
      </div>

      <div className="field">
        <label htmlFor="videoUrl">Video URL</label>
        <input
          id="videoUrl"
          type="url"
          placeholder="https://..."
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
          required
          disabled={disabled}
        />
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="outputDir">Output folder</label>
          <input
            id="outputDir"
            type="text"
            value={outputDir}
            onChange={(e) => setOutputDir(e.target.value)}
            disabled={disabled}
          />
        </div>
        <div className="field">
          <label htmlFor="modelHint">Model preset</label>
          <select
            id="modelHint"
            value={modelHint}
            onChange={(e) => setModelHint(e.target.value)}
            disabled={disabled}
          >
            <option value="default">Balanced</option>
            <option value="fast">Fast</option>
            <option value="accurate">Accuracy-first</option>
          </select>
        </div>
      </div>

      <p className="helper">
        The Python engine will download media, extract audio, run speech rhythm checks, flag
        sensitive words, analyze keyboard sounds, and append OpenFace results to the transcript.
      </p>
    </form>
  );
}
