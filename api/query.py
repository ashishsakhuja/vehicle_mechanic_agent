# api/query.py

import json
from http import HTTPStatus

# import and instantiate your agent exactly how you do in server.py
from src.auto_mechanic_agent2.server import agent

def handler(request):
    # Vercel gives you `request` with .method, .json() etc.
    if request.method != "POST":
        return {
            "statusCode": HTTPStatus.METHOD_NOT_ALLOWED,
            "body": json.dumps({"error": "only POST allowed"})
        }

    payload = request.json or {}
    q = payload.get("query","").strip()
    if not q:
        return {
            "statusCode": HTTPStatus.BAD_REQUEST,
            "body": json.dumps({"error": "query is required"})
        }

    try:
        result = agent.query(q)
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
