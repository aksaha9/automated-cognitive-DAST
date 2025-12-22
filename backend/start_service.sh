#!/bin/bash
echo "Starting ZAP Daemon..."
# Start ZAP in background
# -daemon: Headless
# -port 8090: Default ZAP port
# -host 0.0.0.0: Bind to all interfaces (important for sidecar/localhost comms?)
# Actually for single container, 127.0.0.1 is fine, but 0.0.0.0 is safer.
# -config api.disablekey=true: Disable API key for internal usage (or use generated one)
# We need to match config.ini settings. config.ini uses 'zap_api_key' if set.
# For Cloud Run, simplest is disable key or use fixed one.
# Set Memory Limit for ZAP (Java)
export _JAVA_OPTIONS="-Xmx2g"
zap.sh -daemon -port 8090 -host 127.0.0.1 -config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true &

# Wait for ZAP to be ready
echo "Waiting for ZAP..."
timeout 60 bash -c 'until echo > /dev/tcp/127.0.0.1/8090; do sleep 1; done'
echo "ZAP is ready."

# Start FastAPI
# Cloud Run expects listening on $PORT (default 8080)
PORT=${PORT:-8080}
echo "Starting Uvicorn on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
