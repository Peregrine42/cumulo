#! /bin/bash

rm -rf /etc/keepalived/*
cat > /etc/keepalived/keepalived.conf <<EOF
#vrrp_script chk_kubelet {
  #script "echo"
  #interval 2
#}
vrrp_script chk_kubelet {
  script "curl 127.0.0.1:2379/v2/keys"
  interval 2
}

vrrp_instance VI_1 {
  interface enp0s8
  state $BACKUP_OR_MASTER
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
