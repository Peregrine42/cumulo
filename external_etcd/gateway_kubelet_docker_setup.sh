#! /bin/bash

rm -rf /etc/kubernetes/apiserver
rm -rf /etc/kubernetes/config
rm -rf /etc/kubernetes/controller-manager
rm -rf /etc/kubernetes/kubelet
rm -rf /etc/kubernetes/proxy
rm -rf /etc/kubernetes/scheduler

cat > /etc/kubernetes/kubelet <<EOF
KUBELET_ADDRESS="--address=$IP"
KUBELET_HOSTNAME="--hostname-override=$IP"
#KUBELET_API_SERVER="--api-servers=http://192.168.33.100:8080"
KUBELET_ARGS="--config=/etc/kubernetes/manifests"
EOF

mkdir -p /etc/kubernetes/manifests
rm -rf /etc/kubernetes/manifests/*
cat > /etc/kubernetes/manifests/nginx.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  hostNetwork: true
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
EOF

systemctl enable kubelet
systemctl restart kubelet

systemctl enable docker
systemctl restart docker
