#!/bin/bash
# this script is used to boot a Docker container
echo Started
source venv/bin/activate

if [[ $FLASK_CONFIG == "testing" ]]; then
    echo "running via test config"
    flask test
else
    echo "running via non test cofig"
    while true; do
        flask db upgrade
        if [[ "$?" == "0" ]]; then
            break
        fi
        echo Deploy command failed, retrying in 5 secs...
        sleep 5
    done
    flask deploy
    exec gunicorn -b :5000 --access-logfile - --error-logfile - flasky:app
fi