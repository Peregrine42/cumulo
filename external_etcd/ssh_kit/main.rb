require 'sshkit'
require 'sshkit/dsl'
include SSHKit::DSL

SSHKit::Backend::Netssh.configure do |ssh|
  ssh.ssh_options = {
    user: 'cumulo',
    auth_methods: ['publickey']
  }
end

SSHKit::Backend::Netssh.config.pty = true

hosts = File.readlines('hosts').map do |line|
  line.chomp
end

on hosts, in: :parallel do |host|
  execute 'sudo yum install -y keepalived'
  upload! 'templates/keepalived.conf', '/etc/keepalived/keepalived.conf'
end
