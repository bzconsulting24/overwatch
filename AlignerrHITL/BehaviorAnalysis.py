def interpret_behavior(features):
    def safe_get(col_name):
        return features[col_name].values[0] if col_name in features.columns else None

    pitch = safe_get("F0final_sma_amean")
    energy = safe_get("pcm_RMSenergy_sma_amean")
    jitter = safe_get("jitterLocal_sma_amean")

    results = []
    results.append(f"Pitch (F0final_sma_amean): {pitch:.2f}" if pitch is not None else "Pitch: N/A")
    results.append(f"Energy (RMSenergy): {energy:.2f}" if energy is not None else "Energy: N/A")
    results.append(f"Jitter (local): {jitter:.4f}" if jitter is not None else "Jitter: N/A")

    if pitch is not None and pitch < 120:
        results.append("[warning] Possibly monotone or calm.")
    if energy is not None and energy < -30:
        results.append("[warning] Low vocal energy detected.")
    if jitter is not None and jitter > 0.01:
        results.append("[warning] Unstable voice — could indicate nervousness.")
    elif jitter is not None:
        results.append("[check] Vocal delivery seems stable.")

    print("\n".join(results))
    return results 
