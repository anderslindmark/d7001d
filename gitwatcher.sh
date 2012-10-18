#!/bin/bash

# Put:
#   */5 * * * * /path/to/gitwatcher
# in crontab to check every five minutes

WORKDIR=/home/ubuntu/project

cd $WORKDIR
# Update from remote
git fetch origin

# Get list of changes
LOG=`git log head..origin/master --oneline`

# Check if anything has been done
if [[ "$LOG" != "" ]]; then
	echo "There were new revisions."

	echo "Merging changes"
	git merge origin master
	
	echo -n "Stopping service... "
	PID=`ps a | grep sensorDataHandler.py | grep -v grep | awk '{print $1}'`
	if [[ "$PID" != "" ]]; then
		kill $PID
		echo "Done"
	else
		echo "No service found"
	fi
	
	echo "Starting service"
	$WORKDIR/run
else
	echo "No new revisions"
fi

