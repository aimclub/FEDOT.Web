#!/bin/bash
if [[ $(ps --no-headers -o comm 1) == "systemd" ]]
then
	sudo systemctl start mongod
	sudo systemctl status mongod
else
	sudo service mongod start
	sudo service mongod status
fi
mongo test_db
