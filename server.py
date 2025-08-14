# server.py
import os
import sys
import re
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ── Make sure Python can see your src/ tree ─────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Use an absolute path for the built UI to avoid CWD issues
STATIC_DIR = os.path.join(HERE, "ui", "dist")

# ── Flask app setup ────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    static_url_path=""  # serve /index.html, /assets/*, etc. at site root
)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Vehicle extractor (year + make + model) ────────────────────────
def extract_vehicle(text: str) -> str:
    """
    Return a concise 'YYYY Make Model' (or closest we can get) from free text.
    Lightweight heuristic good enough for image prompts.
    """
    if not text:
        return ""

    makes = {
        "toyota","honda","ford","chevrolet","chevy","nissan","tesla","bmw","mercedes",
        "mercedes-benz","audi","volkswagen","vw","hyundai","kia","subaru","mazda",
        "lexus","acura","infiniti","volvo","porsche","jaguar","land rover","range rover",
        "ram","dodge","jeep","gmc","cadillac","buick","mini","mitsubishi","genesis",
        "alfa romeo","alfa-romeo","fiat","lincoln","saab","scion","smart"
    }

    t = (text or "").lower()

    # Year: prefer a 4-digit 19xx/20xx
    year = None
    m_year = re.search(r"\b(19|20)\d{2}\b", t)
    if m_year:
        year = m_year.group(0)

    # Find first make mention (longer names first)
    found_make = None
    found_span = None
    for mk in sorted(makes, key=len, reverse=True):
        idx = t.find(mk)
        if idx != -1:
            found_make = mk
            found_span = (idx, idx + len(mk))
            break

    if not found_make:
        return (year or "").strip()

    # Grab up to 3 tokens after make as model, stopping at non-model words
    tail = t[found_span[1]:].strip()
    model_tokens = []
    stop_words = {
        "brake","radiator","battery","oil","change","replace","front","rear","left","right",
        "fix","repair","disc","rotor","pad","engine","transmission","how","do","i","need","to",
        "ac","air","filter","spark","plugs","coolant","fluid","door","window","seat","wheel"
    }
    for token in re.split(r"[^a-z0-9\-]+", tail):
        if not token:
            continue
        if token in stop_words:
            break
        model_tokens.append(token)
        if len(model_tokens) >= 3:
            break

    # Normalize case
    make_title = " ".join(w.capitalize() for w in found_make.replace("-", " ").split())
    model = " ".join(model_tokens).upper() if model_tokens else ""

    if year and model:
        return f"{year} {make_title} {model}".strip()
    if year:
        return f"{year} {make_title}".strip()
    if model:
        return f"{make_title} {model}".strip()
    return make_title.strip()

# ── Serve frontend (SPA) ───────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_ui(path: str):
    # If a real file exists in dist/, serve it; otherwise return index.html (SPA)
    full_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# ── /api/query ─────────────────────────────────────────────────────
@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json(silent=True) or {}
    q = (data.get("query") or "").strip()
    if not q:
        print("❌ Empty query received", flush=True)
        return jsonify({"error": "Query is required"}), 400

    try:
        print("✅ Received query:", q, flush=True)

        from auto_mechanic_agent2.crew import AutoMechanicAgent
        print("✅ Imported AutoMechanicAgent", flush=True)

        crew = AutoMechanicAgent().crew()
        print("✅ Crew created", flush=True)

        output_obj = crew.kickoff(inputs={"problem": q})
        print("✅ Crew output received", flush=True)

        raw = output_obj.output if hasattr(output_obj, "output") else str(output_obj)
        print("🔄 Raw output preview:", raw[:500], flush=True)

        m = re.search(r"\{[\s\S]*\}$", raw)
        if not m:
            raise ValueError("Could not extract JSON from agent output")

        result = json.loads(m.group(0))
        print("✅ Parsed result keys:", list(result.keys()), flush=True)

        return jsonify(result)

    except Exception as e:
        print("❌ Exception in /api/query:", repr(e), flush=True)
        return jsonify({"error": str(e)}), 500

# ── /api/generate-image (OpenAI Images: DALL·E 3) ─────────────────
# Accepts { query } or { vehicle }. Generates ONLY the car (no people/background clutter).
@app.route("/api/generate-image", methods=["POST"])
def generate_image():
    data = request.get_json(silent=True) or {}
    vehicle = (data.get("vehicle") or "").strip()
    if not vehicle:
        # Prefer pulling from the user's original query if provided
        vehicle = extract_vehicle((data.get("query") or data.get("prompt") or "").strip())

    if not vehicle:
        return jsonify({"error": "Could not detect vehicle make/model/year from input."}), 400

    # Clean, car-only prompt for DALL·E 3
    prompt = (
        f"Photorealistic studio photograph of a {vehicle}, front three-quarter view, "
        "neutral seamless background, softbox lighting, no people, no text, "
        "no watermarks, centered framing, high detail, sharp focus."
    )

    # DALL·E 3 supported sizes: 1024x1024, 1024x1792 (tall), 1792x1024 (wide)
    size = "1792x1024"  # wide hero

    try:
        from openai import OpenAI
        client = OpenAI()  # uses OPENAI_API_KEY from env

        print(f"🖼️ DALL·E 3 generating {size} for vehicle: {vehicle}", flush=True)

        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size
        )

        # Log the full response for debugging
        print("full openai image response:", resp, flush=True)

        # DALL·E 3 may return a base64 image or a temporary URL
        first = resp.data[0]
        b64 = getattr(first, "b64_json", None)
        url = getattr(first, "url", None)

        if b64:
            print(f"✅ Image base64 length: {len(b64)}", flush=True)
            return jsonify({"image_b64": b64, "vehicle": vehicle})

        if url:
            print(f"✅ Image URL returned: {url}", flush=True)
            # URL is a temporary signed link; fine for immediate display
            return jsonify({"image_url": url, "vehicle": vehicle})

        print("⚠️ No image data returned from DALL·E 3", flush=True)
        return jsonify({"error": "no_image_from_dalle", "vehicle": vehicle}), 200

    except Exception as e:
        print("❌ Exception in /api/generate-image:", repr(e), flush=True)
        return jsonify({
            "error": "image_generation_failed",
            "message": str(e),
            "vehicle": vehicle
        }), 500

# ── Health check ───────────────────────────────────────────────────
@app.get("/api/healthz")
def healthz():
    return jsonify({"ok": True})

# ── Local dev entrypoint ───────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚗 Running server locally at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port)
