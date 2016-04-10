set :application, 'Cumulo'
set :ssh_options, {:forward_agent => true}
set :default_run_options, {:pty => true}
set :stages, ["vagrant", "blades"]
set :default_stage, "vagrant"
set :scm, :copy
set :templating_paths, "templates"
