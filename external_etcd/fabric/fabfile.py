from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import upload_template
import re

cluster_size = 3
gateway_ip = "192.168.33.100"
env.parallel = True
numbers_to_ips = lambda i: "192.168.33." + str(10+i)
public_ips = map(numbers_to_ips, range(0, cluster_size))

numbers_to_names = lambda i: "etcd" + str(i)
names = map(numbers_to_names, range(0, cluster_size))
etcd_cluster_name = "etcd_cluster_04_2016"
ips_to_peers = lambda peer: peer[0] + "=http://" + peer[1] + ":2380"
etcd_peers = ",".join(map(ips_to_peers, zip(names, public_ips)))

def vagrant():
    result = local('vagrant ssh-config', capture=True)
    env.hosts = map(lambda ip: '%s' % ip, public_ips)
    env.user = re.findall(r'User\s+([^\n]+)', result)[0]
    env.key_filename = \
	re.findall(r'IdentityFile\s+"([^"]+)', result)[0]

def update():
    sudo("yum update -y")

def keepalived(template_file):
    primary = env.host == public_ips[0]
    with settings(user='root', password='vagrant'):
	run("yum install -y keepalived")
	run("rm -rf /etc/keepalived/*")
	upload_template(
	    template_file, 
	    "/etc/keepalived/keepalived.conf",
	    { "priority": 101 if primary else 100,
	      "role": "MASTER" if primary else "BACKUP" }
	)
	run("systemctl restart keepalived")
	run("systemctl enable keepalived")

def kubelet_and_docker():
    with settings(user='root', password='vagrant'):
	run("yum install -y kubernetes")
	run("rm -rf /etc/kubernetes/*")
	run("mkdir -p /etc/kubernetes/manifests")
	upload_template(
	    "templates/kubelet",
	    "/etc/kubernetes/kubelet", 
	    { "ip": env.host,
              "gateway_ip": gateway_ip }
	)
	run("systemctl restart docker")
	run("systemctl enable docker")

	run("systemctl restart kubelet")
	run("systemctl enable kubelet")

def haproxy():
    with settings(user='root', password='vagrant'):
	run("yum install -y haproxy")
	run("rm -rf /etc/haproxy/*")
	run("systemctl restart haproxy")
	run("systemctl enable haproxy")

def etcd():
    with settings(user='root', password='vagrant'):
	run("yum install -y etcd")
	upload_template(
	    "templates/etcd.conf",
	    "/etc/etcd/etcd.conf",
	    { "ip": env.host,
	      "index": public_ips.index(env.host),
	      "etcd_cluster_name": etcd_cluster_name,
              "etcd_initial_cluster_list": etcd_peers
	    }
	)
	run("systemctl restart etcd")
	run("systemctl enable etcd")

def flannel():
    with settings(user='root', password='vagrant'):
	run("yum install -y flannel")
	upload_template(
	    "templates/flannel",
	    "/etc/sysconfig/flanneld"
	)
        upload_template(
            "templates/flannel_config.json",
            "/root/flannel_config.json"
	)
        run("etcdctl set /coreos.com/network/config < /root/flannel_config.json")
	run("systemctl restart flanneld")
	run("systemctl enable flanneld")
        run("mkdir -p /etc/systemd/system/docker.service.d")
        upload_template(
            "templates/flannel_dropin.conf",
            "/etc/systemd/system/docker.service.d/flannel.conf"
	)
        run("systemctl daemon-reload")
        run("systemctl stop docker")
	run("ip link delete docker0 | echo")
        run("systemctl start docker")

def demo_keepalived():
    keepalived("templates/demo/keepalived_no_check.conf");

def demo_nginx():
    with settings(user='root', password='vagrant'):
	upload_template(
	    "templates/demo/nginx_manifest.yaml",
	    "/etc/kubernetes/manifests/nginx.yaml"
	)

def demo_haproxy_config():
    with settings(user='root', password='vagrant'):
	upload_template(
	    "templates/demo/haproxy.cfg",
	    "/etc/haproxy/haproxy.cfg"
	)
	run("systemctl restart haproxy")
    

def demo_1():
    update();
    demo_keepalived();

def demo_2():
    demo_1();
    kubelet_and_docker();
    demo_nginx();
    haproxy();
    demo_haproxy_config();

def demo_3():
    demo_2();
    etcd();

def stage_1():
    update();
    keepalived("templates/keepalived.conf");
    kubelet_and_docker();
    haproxy();
    haproxy_conf();
    etcd();

def stage_2():
    flannel();
    apiserver();
    control_manager();
    scheduler();
    proxy();
