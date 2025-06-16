#!/bin/sh
# Run hypercorn directly since packages are installed globally in container
#the number of workers has no big impact, uvloop in theory should be faster but in my test was equal.
#uvicorn should be faster than hypercorn with uvloop as it has less overhead but hypercorn has better protocol negotiotation.
#in this application we have many clients with only one request each so it is better to use "gunicorn + uvicorn"
gunicorn "src.shipment_tracker_api.main:create_app()" \
    --bind 0.0.0.0:8000 \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 16 \
    --access-logfile - \
    --error-log -