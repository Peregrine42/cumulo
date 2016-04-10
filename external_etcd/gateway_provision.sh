#! /bin/bash

yum update -y

yum install -y keepalived
yum install -y kubernetes
yum install -y etcd
yum install -y flannel
yum install -y haproxy

yum remove -y firewalld
yum remove -y iptables-services
