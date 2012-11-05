from tempfile import mkstemp
import os
import shlex
import subprocess

CMD_BASE = "/home/ubuntu/process64/process64 "

def getCarType(raw_data):
	"""
	Use process64 to calculate cartype using the raw_data field of a packet.
	"""
	# Write the file to a tempfile
	_, tmpfile = mkstemp()
	file = open(tmpfile, 'wb')	
	file.write(raw_data)
	file.close()

	# Execute process64
	cmd = CMD_BASE + "-f type -n 1 " + tmpfile
	print "(DEBUG rawdata.py:getCarType) cmd: ", cmd
	cmd = shlex.split(cmd)
	p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
	# Get output
	line = p.stdout.readline().strip()
	for line in p.stdout.readlines():
		pass
	retval = p.wait()

	# Cleanup
	os.remove(tmpfile)

	# Check return value
	if retval == 0:
		return line
	else:
		return None

def getAvgSpeed(path, files):
	"""
	Takes a set of files containing raw data and process them using process64.
	Cleans up the files afterwards.
	"""
	# Build command args for process64
	numfiles = len(files)
	cmd = CMD_BASE + "-f speed -n " + str(numfiles) + " "
	for file in files:
		cmd += file + " "
	
	print "(DEBUG rawdata.py:getAvgSpeed) cmd: ", cmd

	# Execute process64
	cmd = shlex.split(cmd)
	p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)

	# Get first line
	line = p.stdout.readline().strip()
	# Fetch but ignore the rest (so that .wait() will finish)
	for line in p.stdout.readlines():
		pass

	retval = p.wait()

	# Clean up
	for file in files:
		os.remove(file)

	os.rmdir(path)

	# Check return value
	if retval == 0:
		error, min, max, avg = line.split()
		return (min, max, avg)
	else:
		return None
