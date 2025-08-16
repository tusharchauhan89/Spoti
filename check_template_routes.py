import os
import re
import importlib.util
from flask import Flask

# Path to your main Flask app
APP_FILE = "app.py"  # change if it's in another file

# Import your Flask app
spec = importlib.util.spec_from_file_location("app", APP_FILE)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Get defined endpoints in Flask
if hasattr(app_module, "app") and isinstance(app_module.app, Flask):
    app = app_module.app
else:
    raise RuntimeError("No Flask app instance named 'app' found in app.py")

defined_routes = set(app.view_functions.keys())

# Regex to find url_for('endpoint'...)
url_for_pattern = re.compile(r"url_for\(['\"]([a-zA-Z0-9_]+)['\"]")

used_routes = set()

for root, _, files in os.walk("templates"):
    for file in files:
        if file.endswith(".html"):
            with open(os.path.join(root, file), encoding="utf-8") as f:
                content = f.read()
                matches = url_for_pattern.findall(content)
                used_routes.update(matches)

print("✅ Defined routes in Flask app:", defined_routes)
print("📌 Routes used in templates:", used_routes)

missing_routes = used_routes - defined_routes
if missing_routes:
    print("\n❌ Missing routes (used in templates but not defined in Flask):")
    for route in missing_routes:
        print(f" - {route}")
else:
    print("\n🎉 No missing routes found!")
