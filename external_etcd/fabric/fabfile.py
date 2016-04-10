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
    with settings(user='root', password='vagrant'):
	run("yum install -y keepalived")
	run("rm -rf /etc/keepalived/*")
	upload_template(
	    template_file, 
	    "/etc/keepalived/keepalived.conf",
	    { "priority": 100 + public_ips.index(env.host),
	      "role": "BACKUP" }
	)
        upload_template(
            "templates/keepalived_to_master.sh",
            "/etc/keepalived/to_master.sh",
            {},
            mirror_local_mode=True
        )
        upload_template(
            "templates/keepalived_to_backup.sh",
            "/etc/keepalived/to_backup.sh",
            {},
            mirror_local_mode=True
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
        run("systemctl restart kubelet")

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
    
def apiserver():
    with settings(user='root', password='vagrant'):
	upload_template(
	    "templates/kube-apiserver.yaml",
	    "/etc/kubernetes/manifests/kube-apiserver.yaml",
            { "gateway_ip": gateway_ip }
	)

def set_kubelet_to_apiserver():
    with settings(user='root', password='vagrant'):
        upload_template(
            "templates/kubelet-talking-to-api",
            "/etc/kubernetes/kubelet",
	    { "ip": env.host,
              "gateway_ip": gateway_ip }
        )

def control_manager():
    with settings(user='root', password='vagrant'):
        upload_template(
           "templates/kube-controller-manager.yaml",
           "/etc/kubernetes/manifests/kube-controller-manager.yaml",
           { "gateway_ip": gateway_ip }
        )

def scheduler():
    with settings(user='root', password='vagrant'):
        upload_template(
           "templates/kube-scheduler.yaml",
           "/etc/kubernetes/manifests/kube-scheduler.yaml",
           { "gateway_ip": gateway_ip }
        )

def proxy():
    with settings(user='root', password='vagrant'):
        upload_template(
           "templates/kube-proxy.yaml",
           "/etc/kubernetes/manifests/kube-proxy.yaml",
           { "gateway_ip": gateway_ip }
        )

def sky_dns():
    local("np")
    local("mkdir -p tmp")
    with open('templates/sky_dns.yaml', 'r') as template:
        template_contents = template.read()
    with open('tmp/sky_dns.yaml', 'w') as tempfile:
        tempfile.write(template_contents % (gateway_ip))
    local("kubectl create -f tmp/sky_dns.yaml")

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
    set_kubelet_to_apiserver();
    control_manager();
    scheduler();
    proxy();

def stage_3():
    sky_dns();
