set :use_sudo, true
set :run_method, :sudo

set :ssh_options, {
  forward_agent: true, 
  keys: ['~/.vagrant.d/insecure_private_key']
}
set :deploy_to, '/vagrant'
set :gateway_ip, '192.168.33.100'

3.times do |i|
  ip = "192.168.33.#{10+i}"
  server ip, roles: :gatekeeper, ip: ip, user: 'vagrant'
end
