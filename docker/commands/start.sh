#!/bin/bash

case "$ENV" in
"DEV")
    uvicorn main:app --host 0.0.0.0 --port 8002 --log-level debug --reload
    ;;
"PRODUCTION")
    gunicorn main:app --bind 0.0.0.0:8002 --workers $GUNICORN_WORKERS --timeout $GUNICORN_TIMEOUT --log-level info --worker-class uvicorn.workers.UvicornWorker
    ;;
*)
    echo "NO ENV SPECIFIED!"
    exit 1
    ;;
esac
