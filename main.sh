#!/bin/bash

# Start the first process
# gunicorn src.website:app &
source venv/bin/activate
# Start the second process
python3 src/dv_main.py &

python3 src/wfnm_main.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?