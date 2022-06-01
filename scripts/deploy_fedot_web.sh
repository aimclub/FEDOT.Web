#!/bin/bash
cd ..
# backend
export MONGO_CONN_STRING="mongodb://127.0.0.1:27017/test_db?compressors=disabled&gssapiServiceName=mongodb"
sh ./scripts/start_mongo.sh
./venv/bin/python ./init_db.py
# frontend
export REACT_APP_BASE_URL="https://fedot.onti.actcognitive.org:443"
(cd ./frontend || return; npm install && yarn build)
git restore ./frontend/build/static/cases_icons/*
# start
./venv/bin/python ./main.py
