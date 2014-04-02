#!/usr/bin/python

import sys, subprocess, re, os, stat
import logging
from pipes import quote
sys.path.append("@FENCEAGENTSLIBDIR@")
from fencing import *

#BEGIN_VERSION_GENERATION
RELEASE_VERSION="Fence agent for Intel AMT"
REDHAT_COPYRIGHT=""
BUILD_DATE=""
#END_VERSION_GENERATION

def get_power_status(_, options):
	cmd = create_command(options, "status")

	try:
		logging.debug("Running: %s" % cmd)
		process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	except OSError:
		fail_usage("Amttool not found or not accessible")

	process.wait()

	out = process.communicate()
	process.stdout.close()
	process.stderr.close()
	logging.debug("%s\n" % str(out))

	match = re.search('Powerstate:[\\s]*(..)', str(output))
	status = match.group(1) if match else None

	if (status == None):
		return "fail"
	elif (status == "S0"): # SO = on; S3 = sleep; S5 = off
		return "on"
	else:
		return "off"

def set_power_status(_, options):
	cmd = create_command(options, options["--action"])

	try:
		logging.debug("Running: %s" % cmd)
		process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	except OSError:
		fail_usage("Amttool not found or not accessible")

	process.wait()

	out = process.communicate()
	process.stdout.close()
	process.stderr.close()
	logging.debug("%s\n" % str(out))

	return

def reboot_cycle(_, options):
	cmd = create_command(options, "cycle")

	try:
		logging.debug("Running: %s" % cmd)
		process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	except OSError:
		fail_usage("Amttool not found or not accessible")

	status = process.wait()

	out = process.communicate()
	process.stdout.close()
	process.stderr.close()
	logging.debug("%s\n" % str(out))
    
	return not bool(status)

def create_command(options, action):
	# --password / -p
	cmd = "AMT_PASSWORD=" + quote(options["--password"])

	cmd += " " + options["--amttool-path"]

	# --ip / -a
	cmd += " " + options["--ip"]

	# --action / -o
	if action == "status":
		cmd += " info"
	elif action == "on":
		cmd = "echo \"y\"|" + cmd
		cmd += " powerup"
	elif action == "off":
		cmd = "echo \"y\"|" + cmd
		cmd += " powerdown"
	elif action == "cycle":
		cmd = "echo \"y\"|" + cmd
		cmd += " powercycle"
	if action in ["on", "off", "cycle"] and options.has_key("--boot-option"):
		cmd += options["--boot-option"]

	# --use-sudo / -d
	if options.has_key("--use-sudo"):
		cmd = SUDO_PATH + " " + cmd

	return cmd

def define_new_opts():
	all_opt["boot_option"] = {
		"getopt" : "b:",
		"longopt" : "boot-option",
		"help" : "-b, --boot-option=[option]     Change the default boot behavior of the machine. (pxe|hd|hdsafe|cd|diag)",
		"required" : "0",
		"shortdesc" : "Change the default boot behavior of the machine.",
		"choices" : ["pxe", "hd", "hdsafe", "cd", "diag"],
		"order" : 1
	}
	all_opt["amttool_path"] = {
		"getopt" : "i:",
		"longopt" : "amttool-path",
		"help" : "--amttool-path=[path]          Path to amttool binary",
		"required" : "0",
		"shortdesc" : "Path to amttool binary",
		"default" : "@AMTTOOL_PATH@",
		"order": 200
	}

def main():
	atexit.register(atexit_handler)

	device_opt = [ "ipaddr", "no_login", "passwd", "boot_option", "no_port",
		"sudo", "amttool_path", "method" ]

	define_new_opts()

	options = check_input(device_opt, process_input(device_opt))

	docs = { }
	docs["shortdesc"] = "Fence agent for AMT"
	docs["longdesc"] = "fence_amt is an I/O Fencing agent \
which can be used with Intel AMT. This agent calls support software amttool\
(http://www.kraxel.org/cgit/amtterm/)."
	docs["vendorurl"] = "http://www.intel.com/"
	show_docs(options, docs)

	if not is_executable(options["--amttool-path"]):
		fail_usage("Amttool not found or not accessible")

	result = fence_action(None, options, set_power_status, get_power_status, None, reboot_cycle)

	sys.exit(result)

if __name__ == "__main__":
	main()
