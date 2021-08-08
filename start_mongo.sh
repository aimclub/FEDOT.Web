#!/bin/bash
sudo systemctl start mongod
sudo systemctl status mongod
mongo test_db
