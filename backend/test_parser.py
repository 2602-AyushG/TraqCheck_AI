from parser import extract_text, parse_resume
import json
import glob

sample_files = glob.glob("uploads/*.pdf") + glob.glob("uploads/*.docx")

for f in sample_files:
    print(f"--- {f} ---")

    text = extract_text(f)
    result = parse_resume(text)

    print(json.dumps(result, indent=2))
    print()