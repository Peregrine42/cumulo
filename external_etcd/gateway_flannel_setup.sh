#! /bin/bash

cat > /etc/sysconfig/flannel <<EOF
FLANNEL_ETCD="http://192.168.33.100:2379"
FLANNEL_ETCD_KEY="/coreos.com/network"
FLANNEL_OPTIONS="--iface=enp0s8"
EOF

curl --max-time 1 http://192.168.33.100:2379/v2/keys/coreos.com/network/config -XPUT -d value='
{
  "Network": "42.42.0.0/16",
	"SubnetLen": 24,
	"Backend": {
		"Type": "vxlan",
		"VNI": 1
	}
}'

systemctl start flanneld
systemctl enable flanneld

# convince docker to use flannel's bridge as a gateway
mkdir -p /etc/systemd/system/docker.service.d
cat > /etc/systemd/system/docker.service.d/flannel.conf <<EOF
[Service]
EnvironmentFile=-/run/flannel/subnet.env
ExecStart=
ExecStart=/bin/sh -c '/usr/bin/docker daemon \$OPTIONS \
          --bip=\${FLANNEL_SUBNET} --mtu=\${FLANNEL_MTU} \
          \$DOCKER_STORAGE_OPTIONS \
          \$DOCKER_NETWORK_OPTIONS \
          \$ADD_REGISTRY \
          \$BLOCK_REGISTRY \
          \$INSECURE_REGISTRY \
          2>&1 | /usr/bin/forward-journald -tag docker'
EOF

systemctl daemon-reload

systemctl stop docker
ip link delete docker0
systemctl start docker
