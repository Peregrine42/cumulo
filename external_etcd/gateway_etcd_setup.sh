#! /bin/bash

cat > /etc/etcd/etcd.conf <<EOF
# [member]
ETCD_NAME=etcd$INDEX
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"
ETCD_LISTEN_PEER_URLS="http://0.0.0.0:2380"
ETCD_LISTEN_CLIENT_URLS="http://0.0.0.0:2379"

#[cluster]
ETCD_INITIAL_CLUSTER_STATE="new"
ETCD_INITIAL_CLUSTER_TOKEN="$ETCD_CLUSTER_NAME"
ETCD_INITIAL_ADVERTISE_PEER_URLS="\
http://$IP:2380\
"
ETCD_INITIAL_CLUSTER="$ETCD_INITIAL_CLUSTER_LIST"
ETCD_ADVERTISE_CLIENT_URLS="\
http://$IP:2379\
"
ETCD_ADVERTISE_PEER_URLS="\
http://$IP:2380\
"

#[logging]
ETCD_DEBUG="true"
EOF

systemctl enable etcd
systemctl restart etcd
