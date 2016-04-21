require 'erubis'
require 'fileutils'

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
  'payload/primary/etc/keepalived',
  'keepalived.conf'
)

build_config(
  'templates/keepalived.conf.eruby', {
    priority: 100,
    role: 'BACKUP',
    virtual_ip: virtual_ip,
    interface: interface
  },
  'payload/secondary/etc/keepalived',
  'keepalived.conf'
)

['primary', 'secondary'].each do |type|
  build_config(
    'templates/keepalived_systemd_override.conf', 
    {},
    "payload/#{type}/etc/systemd/system/keepalived.conf.d",
    'override.conf'
  )
end
