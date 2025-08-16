import os
import re
import importlib.util
from flask import Flask

# --- CONFIG ---
TEMPLATES_DIR = "backend/templates"  # Path to your templates folder
APP_FILE = "app.py"          # Path to your main Flask app file

# --- Load Flask app ---
spec = importlib.util.spec_from_file_location("app_module", APP_FILE)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Try to find `app` in the loaded module
if not hasattr(app_module, "app") or not isinstance(app_module.app, Flask):
    raise RuntimeError("Flask app instance not found in {}".format(APP_FILE))

app = app_module.app

# --- Get all defined Flask endpoints ---
defined_endpoints = set(app.view_functions.keys())

# --- Scan templates for url_for() usage ---
used_endpoints = set()
pattern = re.compile(r"url_for\(\s*'([^']+)'")
for root, _, files in os.walk(TEMPLATES_DIR):
    for file in files:
        if file.endswith(".html"):
            with open(os.path.join(root, file), encoding="utf-8") as f:
                for line in f:
                    match = pattern.search(line)
                    if match:
                        used_endpoints.add(match.group(1))

# --- Compare ---
missing = used_endpoints - defined_endpoints

print("\n✅ Defined endpoints in app:", defined_endpoints)
print("\n📌 Endpoints used in templates:", used_endpoints)

if missing:
    print("\n❌ Missing endpoints (used in templates but not defined in app):")
    for m in missing:
        print(f"   - {m}")
else:
    print("\n🎉 All endpoints in templates are correctly defined in the app.")
