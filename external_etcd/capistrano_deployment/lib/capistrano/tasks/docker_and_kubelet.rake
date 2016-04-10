desc "Install Docker & Kubelet"
task :install_docker_and_kubelet do
  on roles(:all) do |host|
    as :root do
      execute :yum, "-y", "kubernetes"
      execute :rm, "-rf", "/etc/kubernetes/*"

      template "kubelet.erb", "/etc/kubernetes/kubelet"

      execute :mkdir, "-p", "/etc/kubernetes/manifests"
      execute :rm, "-rf", "/etc/kubernetes/manifests/*"

      execute :systemctl, "enable", "kubelet"
      execute :systemctl, "restart", "kubelet"

      execute :systemctl, "enable", "docker"
      execute :systemctl, "restart", "docker"
    end
  end
end
