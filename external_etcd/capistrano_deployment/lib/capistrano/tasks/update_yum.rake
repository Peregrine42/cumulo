desc "Update yum"
task :install_yum do
  on roles(:all) do |host|
    as :root do
      execute :yum, "-y", "update"
    end
  end
end
