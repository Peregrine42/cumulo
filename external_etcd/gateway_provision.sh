#! /bin/bash

yum update -y

yum install -y keepalived
yum install -y kubernetes
yum install -y etcd
yum install -y flannel
yum install -y haproxy
