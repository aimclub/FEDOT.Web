from app import db
from app.api.pipelines.service import pipeline_by_uid

from flask import request, jsonify

import json


def check_existing_pipelines():
    pipeline_collection = db["pipelines"]
    pipelines = pipeline_collection.find()
    existing_uids = []
    for pipeline in pipelines:
        uid = pipeline["uid"]
        existing_uids.append(uid)
    return existing_uids


def download_pipeline():
    uid = request.json['uid']

    print('Received uid:', uid, 'Type:', type(uid))
    pipeline = pipeline_by_uid(uid)
    if pipeline is None:
        return "Pipeline not found", 404

    # Saving pipeline in JSON format
    pipeline_json, _ = pipeline.save()
    pipeline_data = json.loads(pipeline_json)

    return jsonify(pipeline_data)
