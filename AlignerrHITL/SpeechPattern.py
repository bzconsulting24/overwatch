def flag_sensitive_words(transcript_path, words_to_flag=["combinatorial", "paradigm", "in computer science"]):
    print("Checking transcript for flagged words...")
    flagged_lines = []
    word_hits = {word: 0 for word in words_to_flag}

    with open(transcript_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            lower_line = line.lower()
            matched_words = [word for word in words_to_flag if word in lower_line]
            if matched_words:
                flagged_lines.append((i, line.strip(), matched_words))
                for word in matched_words:
                    word_hits[word] += 1

    output_lines = []
    if flagged_lines:
        output_lines.append("[Warning!] Flagged words found in transcript:")
        for line_num, content, words in flagged_lines:
            output_lines.append(f"  Line {line_num}: {content}")
            output_lines.append(f"    → Matched: {', '.join(words)}")

        output_lines.append("\nSummary of flagged words:")
        for word, count in word_hits.items():
            output_lines.append(f"  {word}: {count} occurrence(s)")
    else:
        output_lines.append("[check] No flagged words found.")

    print("\n".join(output_lines))
    return output_lines
