from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import upload_template
import re
import sys

with open("gateway") as target_file:
    gateway_ip = target_file.read().splitlines()[0]

with open("hosts") as target_file:
    public_ips = target_file.read().splitlines()

env.parallel = True

numbers_to_names = lambda i: "etcd" + str(i)
names = map(numbers_to_names, range(0, len(public_ips)))
etcd_cluster_name = "etcd_cluster_04_2016"
ips_to_peers = lambda peer: peer[0] + "=http://" + peer[1] + ":2380"
etcd_peers = ",".join(map(ips_to_peers, zip(names, public_ips)))

def vagrant():
    result = local('vagrant ssh-config', capture=True)
    env.hosts = map(lambda ip: '%s' % ip, public_ips)
    env.user = re.findall(r'User\s+([^\n]+)', result)[0]
    env.key_filename = \
	re.findall(r'IdentityFile\s+"([^"]+)', result)[0]

def cumulo():
    env.user = "cumulo"
    env.hosts = public_ips

def update():
    sudo("yum update -y")
    sudo("yum install -y net-tools")
    sudo("yum remove -y firewalld")

def sudo_upload_template(source, target, **kwargs):
    kwargs["use_sudo"] = True
    kwargs["mode"] = "0644"
    upload_template(
        source, 
        target,
        **kwargs
    )
    sudo("chown -R root:root " + target)

def keepalived(template_file):
    other_ips = "\n    ".join(filter(lambda x: x != env.host, public_ips))

    sudo("yum install -y keepalived")
    sudo("rm -rf /etc/keepalived/*")
    sudo_upload_template(
        template_file, 
        "/etc/keepalived/keepalived.conf",
        context={ "priority": 100 + public_ips.index(env.host),
          "gateway_ip": gateway_ip,
          "role": "MASTER",
          "ip": env.host,
          "other_ips": other_ips }
    )
    sudo_upload_template(
        "templates/keepalived_to_master.sh",
        "/etc/keepalived/to_master.sh",
        context={ "gateway_ip": gateway_ip }
    )
    sudo_upload_template(
        "templates/keepalived_to_backup.sh",
        "/etc/keepalived/to_backup.sh",
        context={ "gateway_ip": gateway_ip }
    )
    sudo_upload_template(
        "templates/keepalived_sysctl.conf",
        "/etc/sysctl.conf"
    )
    
    sudo("mkdir -p /etc/systemd/system/keepalived.conf.d")
    sudo_upload_template(
        "templates/keepalived_systemd_override.conf",
        "/etc/systemd/system/keepalived.conf.d/override.conf"
    )

    sudo("systemctl daemon-reload")
    sudo("systemctl restart keepalived")
    sudo("systemctl enable keepalived")

def kubelet_and_docker():
    with settings(user='root', password=password):
	sudo("yum install -y kubernetes")
	sudo("rm -rf /etc/kubernetes/*")
	sudo("mkdir -p /etc/kubernetes/manifests")
	upload_template(
	    "templates/kubelet",
	    "/etc/kubernetes/kubelet", 
	    { "ip": env.host,
              "gateway_ip": gateway_ip }
	)
	sudo("systemctl restart docker")
	sudo("systemctl enable docker")

	sudo("systemctl restart kubelet")
	sudo("systemctl enable kubelet")

def haproxy():
    with settings(user='root', password=password):
	sudo("yum install -y haproxy")
	sudo("rm -rf /etc/haproxy/*")
	sudo("systemctl restart haproxy")
	sudo("systemctl enable haproxy")

def etcd():
    with settings(user='root', password=password):
	sudo("yum install -y etcd")
	upload_template(
	    "templates/etcd.conf",
	    "/etc/etcd/etcd.conf",
	    { "ip": env.host,
	      "index": public_ips.index(env.host),
	      "etcd_cluster_name": etcd_cluster_name,
              "etcd_initial_cluster_list": etcd_peers
	    }
	)
	sudo("systemctl restart etcd")
	sudo("systemctl enable etcd")

def flannel():
    with settings(user='root', password=password):
	sudo("yum install -y flannel")
	upload_template(
	    "templates/flannel",
	    "/etc/sysconfig/flanneld"
	)
        upload_template(
            "templates/flannel_config.json",
            "/root/flannel_config.json"
	)
        sudo("etcdctl set /coreos.com/network/config < /root/flannel_config.json")
	sudo("systemctl restart flanneld")
	sudo("systemctl enable flanneld")

        sudo("mkdir -p /etc/systemd/system/docker.service.d")
        upload_template(
            "templates/flannel_dropin.conf",
            "/etc/systemd/system/docker.service.d/flannel.conf"
	)
        sudo("systemctl daemon-reload")
        sudo("systemctl stop docker")
	sudo("ip link delete docker0 | echo")
        sudo("systemctl start docker")
        sudo("systemctl restart kubelet")

def demo_keepalived():
    keepalived("templates/demo/keepalived_no_check.conf");

def demo_nginx():
    with settings(user='root', password=password):
	upload_template(
	    "templates/demo/nginx_manifest.yaml",
	    "/etc/kubernetes/manifests/nginx.yaml"
	)

def demo_haproxy_config():
    with settings(user='root', password=password):
	upload_template(
	    "templates/demo/haproxy.cfg",
	    "/etc/haproxy/haproxy.cfg"
	)
	sudo("systemctl restart haproxy")
    
def apiserver():
    with settings(user='root', password=password):
	upload_template(
	    "templates/kube-apiserver.yaml",
	    "/etc/kubernetes/manifests/kube-apiserver.yaml",
            { "gateway_ip": gateway_ip }
	)

def set_kubelet_to_apiserver():
    with settings(user='root', password=password):
        upload_template(
            "templates/kubelet-talking-to-api",
            "/etc/kubernetes/kubelet",
	    { "ip": env.host,
              "gateway_ip": gateway_ip }
        )

def control_manager():
    with settings(user='root', password=password):
        upload_template(
           "templates/kube-controller-manager.yaml",
           "/etc/kubernetes/manifests/kube-controller-manager.yaml",
           { "gateway_ip": gateway_ip }
        )

def scheduler():
    with settings(user='root', password=password):
        upload_template(
           "templates/kube-scheduler.yaml",
           "/etc/kubernetes/manifests/kube-scheduler.yaml",
           { "gateway_ip": gateway_ip }
        )

def proxy():
    with settings(user='root', password=password):
        upload_template(
           "templates/kube-proxy.yaml",
           "/etc/kubernetes/manifests/kube-proxy.yaml",
           { "gateway_ip": gateway_ip }
        )

@hosts('localhost')
def sky_dns():
    local("mkdir -p tmp")
    with open('templates/sky_dns.yaml', 'r') as template:
        template_contents = template.read()
    with open('tmp/sky_dns.yaml', 'w') as tempfile:
        tempfile.write(template_contents % { "gateway_ip": gateway_ip })
    local("kubectl delete -f tmp/sky_dns.yaml | echo")
    local("kubectl create -f tmp/sky_dns.yaml | echo")

def haproxy_conf():
    demo_haproxy_config();

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
    execute(sky_dns);
