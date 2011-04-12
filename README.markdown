fabric-server-query
===================
A simple administrator toolkit foundation to get what he wants from farm of servers. More a research project but usefull.
Tested on OSX.

Assumptions
-----------
- Remote commands are exucuted using ssh and keys are registered for no password login (otherwise password prompt is provided).
- Remote user is the same as local and have direct access to all required commands.
With small tuning username can be put in hosts file as a part of hostname.

Implemented metrics
-------------------
### vmstat
A 30 second sample of number of context switches on the host.

### ping
Whether the node is able to reach each of the other nodes

### iostat
A 30 second sample of the average service time for each of the physical disks attached to the node.
svctm for each device

### ps
The top five processes in total cpu time
The top five processes in resident memory usage

### load
The current cpu load of the machine (1 minute average)

### retransmits
Any retransmits on any of its interfaces (netstat -s tcp retransmits)

### homeavgfsize
The average file size per directory under /home (recursive, server side calculation)


setup/installation
------------------
- execute (to download buildout and fabric). (To make buildout compatible with latest OSX I needed to patch it. Makefile automatically patch it. Unfortunately it's not deeply tested on other systems. So in case of buildout issues just remove patching from Makefile)

	make

- edit hosts file

	vi hosts


usage
-----
- full run

	./bin/fab all summary

- help

	./bin/fab -l

- example short run:

	./bin/fab ping ps vmstat summary
