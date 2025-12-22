#!/bin/bash
echo "Starting ZAP Daemon for Ephemeral Job..."
zap.sh -daemon -port 8090 -host 127.0.0.1 -config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true &

echo "Waiting for ZAP..."
timeout 60 bash -c 'until echo > /dev/tcp/127.0.0.1/8090; do sleep 1; done'
echo "ZAP is ready."

echo "Starting Job Runner..."
# Pass all arguments to python script
python3 job_runner.py "$@"
EXIT_CODE=$?

echo "Job finished with exit code $EXIT_CODE"
# ZAP will die when container dies
exit $EXIT_CODE
