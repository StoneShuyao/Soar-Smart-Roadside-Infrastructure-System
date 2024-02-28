#!/bin/bash
# Run multiple parallel instances of iperf servers

# Assumes the port numbers used by the servers start at 5001 and increase
# e.g. 5001, 5002, 5003, ...
# If you want something different, then change the following parameter value
# to be: firstport - 1
base_port=5200

num_servers=12

# Run iperf multiple times
for i in `seq 1 $num_servers`; do

	# Set server port
	server_port=$(($base_port+$i));

	# Run iperf
	iperf3 -s -p $server_port -D
done