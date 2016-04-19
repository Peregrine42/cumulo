#!/bin/bash
 
ip addr add %(gateway_ip)s/32 scope host dev lo
ipvsadm --save > /tmp/keepalived.ipvs
ipvsadm --clear
