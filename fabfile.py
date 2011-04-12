from __future__ import with_statement
from fabric.api import *
from fabric.decorators import runs_once
import re

delay = 30 # final is 30
pingcount = 3 # recommend 3

#env.user = "root"

def _gethosts():
	"""
	helper function to preload hosts list
	"""
	name = "hosts"
	try:
		hosts = open(name)
	except IOError:
		abort('file not found: %s' % name)
	
	return [line.strip() for line in hosts]

env.hosts.extend(_gethosts())
env.summary = dict() #we'll store all outputs here (recommended by fabric)
env.summary_print = dict() #we'll store here a map of visualisation functions


def _extend_summary(host,key,value):
	if not env.summary.has_key(host):
		env.summary[host] = dict()
	env.summary[host][key] = value
	


def _summary_print_value(key,value):
	print "  %s: %s" % (key,value)

def _summary_print_dict(key,value):
	print "  %s:" % key
	for key2 in value.keys():
		print "    %s: %s" % (key2, value[key2])


def vmstat():
	"""
	Req 1) A 30 second sample of number of context switches on the host.
	"""
	vmstat_output = run('vmstat %s 2' % delay)
	lines = vmstat_output.split("\n")
	nodes = re.split(' +', lines[-1].strip())
	cs = nodes[-5]
	_extend_summary(env.host,"cs",cs)
	print cs
env.summary_print["cs"] = _summary_print_value

def ping():
	"""
	Req 2) Whether the node is able to reach each of the other nodes
	"""
	pingable = dict()
	for host in env.hosts:
		if host != env.host:
			if run("ping -c %s %s" % (pingcount,host)).succeeded:
				pingable[host] = True
	_extend_summary(env.host,"pingable",pingable)
	print pingable
env.summary_print["pingable"] = _summary_print_dict


def iostat():
	"""
	Req 3) A 30 second sample of the average service time for each of the physical disks attached to the node.
	svctm for each device
	"""
	devices = dict()
	iostat_out = run("iostat -d -x %s 2" % delay)
	lines = iostat_out.split("\n")
	rnum = 0
	for line in lines:
		nodes = re.split(' +', line.strip())
		if nodes[0] == "Device:":
			rnum += 1
		elif rnum ==2 and len(nodes) > 3: #interval data
			devices[nodes[0]] = nodes[10] #svctm
	_extend_summary(env.host,"devices_svctm",devices)
	print devices	
env.summary_print["devices_svctm"] = _summary_print_dict



def _summary_print_highcpu(key,value):
	print "  %s:" % key
	print "    %5s %10s %7s" % ("pid","comm","cpu")
	for line in value:
		print "    %5s %10s %7s" % (line["pid"],line["comm"],line["cpu"])

def _summary_print_highrss(key,value):
	print "  %s:" % key
	print "    %5s %10s %7s" % ("pid","comm","rss")
	for line in value:
		print "    %5s %10s %7s" % (line["pid"],line["comm"],line["rss"])


def ps():
	"""
	Req 4) The top five processes in total cpu time
	Req 5) The top five processes in resident memory usage
	"""
	highcpu = []
	highrss = []
	ps_cpu_out = run("ps -eo pid,user,pcpu,comm --sort -pcpu --no-headers | head -n 5")
	ps_rss_out = run("ps -eo pid,user,rss,comm --sort -rss --no-headers | head -n 5")
	for line in ps_cpu_out.split("\n"):
		nodes = re.split(' +', line.strip())
		highcpu.append({"pid":nodes[0],"user":nodes[1],"cpu":nodes[2],"comm":nodes[3]})
	for line in ps_rss_out.split("\n"):
		nodes = re.split(' +', line.strip())
		highrss.append({"pid":nodes[0],"user":nodes[1],"rss":nodes[2],"comm":nodes[3]})

	_extend_summary(env.host,"highcpu",highcpu)
	_extend_summary(env.host,"highrss",highrss)
	print highcpu
	print highrss
env.summary_print["highcpu"] = _summary_print_highcpu
env.summary_print["highrss"] = _summary_print_highrss


def load():
	"""
	Req 6) The current cpu load of the machine
	assuming 1 minute average
	"""
	load = None
	uptime_out = run("uptime")
	nodes = re.split('[ ,:]+', uptime_out.strip())
	print nodes
	is_load = False
	for node in nodes: #picking next node after average keyword
		if is_load:
			is_load = False
			load = node
		if node == "average":
			is_load = True
	_extend_summary(env.host,"load",load)
	print load
env.summary_print["load"] = _summary_print_value


def retransmits():
	"""
	Req 7) Any retransmits on any of its interfaces
	I'm assuming we're refering to netstat -s tcp retransmits
	"""
	netstat_out = run("netstat -s | grep 'segments retransmited'")
	nodes = re.split(' +', netstat_out.strip())
	retransmits = nodes[0]
	_extend_summary(env.host,"retransmits",retransmits)
	print retransmits
env.summary_print["retransmits"] = _summary_print_value

def homeavgfsize():
	"""
	Req 8) The average file size per directory under /home
	avg needs to be calculated on server side
	I'm assuming that calculation shall take into account recursive files
	"""
	homeavgs = dict()
	with cd("/home"):
		ls_out = run("ls -1")
		for line in ls_out.split("\n"):
			dir = line.strip()
			avg_fsize = run("find %s -printf '%%s\\n' | gawk '{sum += $1} END {print sum/NR}'" % dir)
			homeavgs[dir] = int(float(avg_fsize))
	_extend_summary(env.host,"homeavgs",homeavgs)
	print homeavgs
env.summary_print["homeavgs"] = _summary_print_dict

def all():
	vmstat()
	ping()
	iostat()
	ps()
	load()
	retransmits()
	homeavgfsize()

@runs_once
def summary():
	"""
	The script should collate the above information into a human readable form.
	"""
	#TODO: add managed display order
	print
	print "Summary"
	print
	for host in env.summary.keys():
		print "host: %s" % host
		for factor in env.summary[host].keys():
			env.summary_print[factor](factor,env.summary[host][factor])
		print
#	print env.summary
	
	