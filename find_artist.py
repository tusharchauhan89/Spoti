import os
import re

TEMPLATES_DIR = "templates"  # adjust if your templates folder is elsewhere
pattern = re.compile(r"url_for\(['\"]search_artist['\"]")

matches = []

for root, _, files in os.walk(TEMPLATES_DIR):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if pattern.search(content):
                    matches.append(path)

if matches:
    print("Found 'url_for(\"search_artist\")' in these files:")
    for m in matches:
        print(" -", m)
else:
    print("No 'search_artist' references found.")
