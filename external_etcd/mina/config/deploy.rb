require 'mina/bundler'

set :domain, 'foobar.com'
set :user, 'vagrant'
set :forward_agent, true     # SSH forward_agent.

# This task is the environment that is loaded for most commands, such as
# `mina deploy` or `mina rake`.
task :environment do
end

task :setup => :environment do
end
