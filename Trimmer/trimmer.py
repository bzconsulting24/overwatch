import re
import pyperclip

# Step 1: Load text file
with open('C:\\Users\\julius\\Documents\\vscode codes\\behaviorAnalysis\\text.txt', 'r', encoding='utf-8') as file:
    text = file.read()

# Step 2: Define pattern (non-capturing group to avoid split pollution)
pattern = r'(?m)^(?:25|50)\n\d\.\d+\sof\s\d+\n+\$\d+'

# Step 3: Split text by matches
split_parts = re.split(pattern, text, flags=re.MULTILINE)

# Step 4: Get last item
last_item = split_parts[-1] if split_parts else ""

# Step 5: Extract before "Case details"
before_case_details = last_item.split("Case details")[0] if "Case details" in last_item else last_item

# Step 6: Trim and copy
result = before_case_details.strip()
pyperclip.copy(result)

print("Done. Extracted content copied to clipboard.")
