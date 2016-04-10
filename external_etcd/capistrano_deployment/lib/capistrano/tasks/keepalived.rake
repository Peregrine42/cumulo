desc "Install keepalived"
task :install_keepalived do
  on roles(:gatekeeper) do |host|
    as :root do
      execute :yum, "-y", "keepalived"
      template(
        "keepalived.conf.erb", 
        "/etc/keepalived/keepalived.conf"
      )

      execute :systemctl, "enable", "keepalived"
      execute :systemctl, "restart", "keepalived"
    end
  end
end
