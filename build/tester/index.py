#!/usr/bin/env python
VERSION = "1.0.0"
RUNTIME = f"python3-k-runner-{VERSION}"
from flask import Flask, request, jsonify
from waitress import serve
import os
import json

import kubiya
from kubiya.action_store import ActionStore
from kubiya.loader import get_single_action_store


from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Json, ValidationError
import traceback

from function import main_store


class Request(BaseModel):
    action: Optional[str]
    input:  Optional[Any]
    secrets: Optional[Dict]
    action_store: Optional[str]
    inbox_id: Optional[str]
    runner: Optional[str]



def execute_handler(request: Request, action_store: ActionStore) -> Any:
    try:
        if request.action == '__KUBIYA_DISCOVER__':
            return {
                "faas_runtime": RUNTIME,
                "name": action_store.get_name(),
                "version": action_store.get_version(),
                "registered_actions": action_store.get_registered_actions(),
                "secrets": action_store.get_registered_secrets(),
                "kubiya_version": "python-sdk: " + kubiya.__version__,
                "actions_metadata": action_store._action_metadata,
            }

        if request.secrets:
            setattr(action_store, "secrets", request.secrets)
        result = action_store.execute_action(request.action, request.input)
        return {"result": result, "faas_runtime": RUNTIME}
    except Exception as e:
        return {
            "error": str(e),
            "stacktrace": traceback.format_exc(),
        }

app = Flask(__name__)

# class Context:
#     def __init__(self):
#         self.hostname = os.getenv('HOSTNAME', 'localhost')

# distutils.util.strtobool() can throw an exception
def is_true(val):
    return len(val) > 0 and val.lower() == "true" or val == "1"



@app.before_request
def fix_transfer_encoding():
    """
    Sets the "wsgi.input_terminated" environment flag, thus enabling
    Werkzeug to pass chunked requests as streams.  The gunicorn server
    should set this, but it's not yet been implemented.
    """

    transfer_encoding = request.headers.get("Transfer-Encoding", None)
    if transfer_encoding == u"chunked":
        request.environ["wsgi.input_terminated"] = True

def get_handler_store():
    return 

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    
    try:
        # data = json.loads(req)
        request = Request.parse_raw(req)
        # (data.get("action"), data.get("input"), data.get("secrets"))

        return {
            "inbox_id": request.inbox_id,
            "runner": request.runner,
            "output": execute_handler(request=request, action_store=get_single_action_store()),
        }

    # return req
    except Exception as e:
        return {
            "error": str(e),
            "stacktrace": traceback.format_exc(),
        }


@app.route("/", defaults={"path": ""}, methods=["POST", "GET"])
@app.route("/<path:path>", methods=["POST", "GET"])
def main_route(path):
    raw_body = os.getenv("RAW_BODY", "false")

    as_text = True

    if is_true(raw_body):
        as_text = False
    
    ret = handle(request.get_data(as_text=as_text))
    
    return ret

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
