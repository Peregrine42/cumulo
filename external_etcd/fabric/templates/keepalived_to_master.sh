#!/bin/bash
 
ip addr del 192.168.33.100/32 dev lo
ipvsadm --restore < /tmp/keepalived.ipvs
