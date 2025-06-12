#!/bin/sh
# Run hypercorn directly since packages are installed globally in container
hypercorn "src.shipment_tracker_api.main:create_app()" --bind 0.0.0.0:8000 --worker-class asyncio