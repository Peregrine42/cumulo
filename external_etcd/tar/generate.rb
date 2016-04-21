require 'erubis'
require 'fileutils'

hosts = [
  '192.168.33.10', 
  '192.168.33.11', 
  '192.168.33.12'
]
primary = '192.168.33.10'
virtual_ip = '192.168.33.100'
interface = 'enp0s8'

def write_template dir, name, output
  FileUtils::mkdir_p dir
  File.open("#{dir}/#{name}", 'w') do |file| 
    file.write(output) 
  end
end

def build_config path, namespace, target_dir, filename
  input = File.read(path)
  eruby = Erubis::Eruby.new(input)
  output = eruby.result(**namespace)
  write_template target_dir, filename, output
end

FileUtils::rm_rf 'payload'

build_config(
  'templates/keepalived.conf.eruby', {
    priority: 101,
    role: 'BACKUP',
    virtual_ip: virtual_ip,
    interface: interface
  },
  "payload/#{primary}/etc/keepalived",
  'keepalived.conf'
)

hosts.each do |host|
  next host if host == primary
  build_config(
    'templates/keepalived.conf.eruby', {
      priority: 100,
      role: 'BACKUP',
      virtual_ip: virtual_ip,
      interface: interface
    },
    "payload/#{host}/etc/keepalived",
    'keepalived.conf'
  )
end

hosts.each do |host|
  type = host == primary ? 'primary' : 'secondary'
  build_config(
    'templates/keepalived_systemd_override.conf', 
    {},
    "payload/#{type}/etc/systemd/system/keepalived.conf.d",
    'override.conf'
  )
end

hosts.each do |host|
  build_config(
    'templates/kubelet_config', 
    { 
			gateway_ip: virtual_ip,
      ip: host
    },
    "payload/#{host}/etc/kubernetes",
    'kubelet'
  )
end

hosts.each do |host|
  build_config(
    'templates/haproxy_config', 
    {},
    "payload/#{host}/etc/haproxy",
    'haproxy.cfg'
  )
end

hosts.each_with_index do |host, index|
  build_config(
    'templates/etcd.conf', 
    {
      index: index,
      cluster_name: "2016-04-21-cumulo-etcd",
      initial_cluster: hosts
        .each_with_index
        .map { |h, i| "etcd#{i}=http://#{h}:2380" }
        .join(","),
      ip: host
    },
    "payload/#{host}/etc/etcd",
    'etcd.conf'
  )
end
