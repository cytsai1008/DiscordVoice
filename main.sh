#!/bin/bash

# Start the first process
gunicorn src.website:app &

# Start the second process
python src/dv_main.py &

python src/wfnm_main.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?