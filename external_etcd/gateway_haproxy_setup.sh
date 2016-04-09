#! /bin/bash

rm -rf /etc/haproxy/*
cat > /etc/haproxy/haproxy.cfg <<EOF
global
  log 127.0.0.1   local0
  log 127.0.0.1   local1 notice
  user haproxy
  group haproxy

defaults
  log     global
  mode    http
  option  httplog
  option  dontlognull
  option forwardfor
  option http-server-close
  contimeout 5000
  clitimeout 50000
  srvtimeout 50000
  errorfile 400 /usr/share/haproxy/400.http
  errorfile 403 /usr/share/haproxy/403.http
  errorfile 408 /usr/share/haproxy/408.http
  errorfile 500 /usr/share/haproxy/500.http
  errorfile 502 /usr/share/haproxy/502.http
  errorfile 503 /usr/share/haproxy/503.http
  errorfile 504 /usr/share/haproxy/504.http
  stats enable
  stats auth admin:password
  stats uri /stats

frontend nginx_demo
  bind *:80
  use_backend nginx_demo_80

backend nginx_demo_80
  option httpclose
  option forwardfor
  option httpchk HEAD / HTTP/1.0
  server nginx 127.0.0.1:8080 check
EOF

systemctl restart haproxy
systemctl enable haproxy
