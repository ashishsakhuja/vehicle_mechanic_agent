import os
import sys
import re
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ─── Make sure Python can see your src/ tree ─────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# ─── Flask app setup ────────────────────────────────────────
app = Flask(
    __name__,
    static_folder="ui/dist",
    static_url_path=""
)
CORS(app)

# ─── Serve frontend ─────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_ui(path):
    full_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# ─── API endpoint with logs ─────────────────────────────────
@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json() or {}
    q = data.get("query", "").strip()
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
        print("🔄 Raw output:", raw[:500], flush=True)  # Limit output preview to 500 chars

        m = re.search(r"\{[\s\S]*\}$", raw)
        if not m:
            raise ValueError("Could not extract JSON from agent output")

        result = json.loads(m.group(0))
        print("✅ Parsed result:", result, flush=True)

        return jsonify(result)

    except Exception as e:
        print("❌ Exception:", str(e), flush=True)
        return jsonify({"error": str(e)}), 500

# ─── Local dev only ─────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚗 Running server locally at http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
