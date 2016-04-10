#!/bin/bash
 
ip addr add 192.168.33.100/32 scope host dev lo
ipvsadm --save > /tmp/keepalived.ipvs
ipvsadm --clear
