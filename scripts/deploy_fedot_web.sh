#!/bin/bash
cd ..
# backend
export MONGO_CONN_STRING="mongodb://127.0.0.1:27017/test_db?compressors=zlib"
# sh ./scripts/start_mongo.sh

./venv/bin/python ./init_db.py
# frontend
export REACT_APP_BASE_URL=https://fedot.onti.actcognitive.org:443
(cd ./frontend || return; npm install && npm audit fix && npx browserslist@latest --update-db && yarn build)
git restore ./frontend/build/static/cases_icons/*
# start
export FLASK_HOST=10.32.1.9
export FLASK_PORT=5000
./venv/bin/python ./main.py
