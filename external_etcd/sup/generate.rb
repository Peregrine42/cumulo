require 'erubis'
require 'fileutils'

input = File.read('templates/keepalived.conf.eruby')
eruby = Erubis::Eruby.new(input)
output = eruby.result(
	priority: 101,
	role: 'MASTER',
  virtual_ip: '192.168.33.100'
)

FileUtils::mkdir_p 'config/primary'
File.open('config/primary/keepalived.conf', 'w') do |file| 
  file.write(output) 
end
