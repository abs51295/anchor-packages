#!/bin/bash
gunicorn --pythonpath /src/ -b 0.0.0.0:$ANCHOR_PACKAGES_SERVICE_PORT -t $ANCHOR_PACKAGES_SERVICE_TIMEOUT -k gevent -w $NUMBER_WORKER_PROCESS flask_api:app