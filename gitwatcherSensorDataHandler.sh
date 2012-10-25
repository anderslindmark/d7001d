#!/bin/bash

# This script checks if there are any changes in git upstream
# If any changes are available it will merge them and restart the service

# Put:
#   */5 * * * * /path/to/gitwatcher
# in crontab to check every five minutes

WORKDIR=/home/ubuntu/project

cd $WORKDIR
# Update from remote
git fetch origin

# Get list of changes
LOG=$(git log HEAD..origin/master)

# Check if anything has been done
if [[ "$LOG" != "" ]]; then
	echo "There were new revisions."
	echo -n "Stopping service... "
	PID=`ps a | grep sensorDataHandler.py | grep -v grep | awk '{print $1}'`
	if [[ "$PID" != "" ]]; then
		kill -9 $PID
		echo "Done"
	else
		echo "No service found"
	fi
	
	echo "Starting service"
	$WORKDIR/runSensorDataHandler &
else
	echo "No new revisions"
fi

