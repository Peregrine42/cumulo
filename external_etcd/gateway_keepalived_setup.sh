#! /bin/bash

cat > /etc/keepalived/keepalived.conf <<EOF
vrrp_script chk_kubelet {
  script "echo" # a dummy checker for now
  interval 2
}

vrrp_instance VI_1 {
  interface enp0s8
  state BACKUP
  virtual_router_id 51
  priority $PRIORITY # 101 on master, 100 on backup
  virtual_ipaddress {
    192.168.33.100 # the virtual IP
  }

  track_script {
    chk_kubelet
  }
}
EOF

systemctl restart keepalived
systemctl enable keepalived