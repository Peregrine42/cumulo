#! /bin/bash

cat > /etc/kubernetes/manifests/nginx.yaml <<EOF
--- 
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  hostNetwork: true
  containers:
  - name: nginx
    image: peregrine42/nginx8080
    ports:
    - containerPort: 8080
EOF
