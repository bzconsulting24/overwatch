from difflib import SequenceMatcher

def flag_sensitive_words(transcript_path, reference_path, threshold=0.85, window_size=8):
    print("Checking transcript for LLM-like phrasing...")
    flagged_lines = []

    # Load LLM-style reference phrases
    with open(reference_path, "r", encoding="utf-8") as ref_file:
        reference_phrases = [line.strip().lower() for line in ref_file if line.strip()]
    phrase_hits = {phrase: 0 for phrase in reference_phrases}

    # Process transcript
    with open(transcript_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            words = line.strip().lower().split()
            for j in range(len(words)):
                for k in range(1, window_size + 1):
                    ngram = " ".join(words[j:j+k])
                    if not ngram:
                        continue
                    for phrase in reference_phrases:
                        similarity = SequenceMatcher(None, ngram, phrase).ratio()
                        if similarity >= threshold:
                            flagged_lines.append((i, ngram, phrase, round(similarity * 100, 2)))
                            phrase_hits[phrase] += 1
                            break
                    else:
                        continue
                    break

    # Report
    output_lines = []
    if flagged_lines:
        output_lines.append("[Warning!] Gemini-style phrases detected:")
        for line_num, found_ngram, matched_phrase, similarity in flagged_lines:
            output_lines.append(f"  Line {line_num}: \"{found_ngram}\" → \"{matched_phrase}\" ({similarity}%)")
        output_lines.append("\nSummary of matched phrases:")
        for phrase, count in phrase_hits.items():
            if count > 0:
                output_lines.append(f"  \"{phrase}\": {count} occurrence(s)")
    else:
        output_lines.append("[check] No Gemini-style phrases found.")

    print("\n".join(output_lines))
    return output_lines
