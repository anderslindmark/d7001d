from tempfile import mkstemp
import os
import shlex
import subprocess

CMD_BASE = "/home/ubuntu/process64/process64 "
CMD_TYPE = "-f type"
CMD_SPEED = "-f speed"

def getCarType(raw_data):
	_, tmpfile = mkstemp()
	file = open(tmpfile, 'wb')	
	file.write(raw_data)
	file.close()

	cmd = CMD_BASE + "-f type " + tmpfile
	print "(DEBUG rawdata.py:getCarType) cmd: ", cmd
	cmd = shlex.split(cmd)
	p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
	line = p.stdout.readline().strip()
	for line in p.stdout.readlines():
		pass
	retval = p.wait()

	os.remove(tmpfile)

	if retval == 0:
		return line
	elif retval == -1:
		# corrupt packet
		pass
	elif retval == -2:
		# bad args
		pass
	else:
		print "Bad retval: %d" % retval

def getAvgSpeed(path, files):
	numfiles = len(files)
	cmd = CMD_BASE + "-f speed -n " + str(numfiles) + " "
	for file in files:
		cmd += path + "/" + file + " "
	
	print "(DEBUG rawdata.py:getAvgSpeed) cmd: ", cmd

	cmd = shlex.split(cmd)
	
	p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)

	# get first line
	line = p.stdout.readline().strip()
	# fetch but ignore the rest (so that .wait() will finish)
	for line in p.stdout.readlines():
		pass

	retval = p.wait()

	# Clean up
	for file in files:
		os.remove(path + "/" + file)

	os.rmdir(path)

	# Check return value
	if retval == 0:
		error, min, max, avg = line.split()
		return avg
	elif retval == -1:
		# corrupt packet
		pass
	elif retval == -2:
		# bad args
		pass
	else:
		print "Bad retval: %d" % retval
