#!/bin/bash
 
ip addr del %(gateway_ip)s/32 dev lo
ipvsadm --restore < /tmp/keepalived.ipvs
