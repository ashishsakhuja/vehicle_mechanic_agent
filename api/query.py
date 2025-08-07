# api/query.py

import os
import sys
import json
import re
from http import HTTPStatus

# ─── Ensure src/ is in sys.path ─────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# ─── Import your agent class ────────────────────────────────
from auto_mechanic_agent2.crew import AutoMechanicAgent

def handler(request):
    # Vercel gives you `request` with .method, .json, etc.
    if request.method != "POST":
        return {
            "statusCode": HTTPStatus.METHOD_NOT_ALLOWED,
            "body": json.dumps({"error": "Only POST is allowed"})
        }

    payload = request.json or {}
    q = payload.get("query", "").strip()
    if not q:
        return {
            "statusCode": HTTPStatus.BAD_REQUEST,
            "body": json.dumps({"error": "Query is required"})
        }

    try:
        # Run the agent just like in server.py
        crew = AutoMechanicAgent().crew()
        output_obj = crew.kickoff(inputs={"problem": q})

        raw = output_obj.output if hasattr(output_obj, "output") else str(output_obj)

        m = re.search(r"\{[\s\S]*\}$", raw)
        if not m:
            raise ValueError("Could not extract JSON from agent output")

        result = json.loads(m.group(0))

        return {
            "statusCode": HTTPStatus.OK,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }

    except Exception as e:
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": json.dumps({"error": str(e)})
        }
