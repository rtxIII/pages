apt -y update
apt -y install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
apt remove docker docker-engine docker.io containerd runc
# Add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/trusted.gpg.d/docker-archive-keyring.gpg

# Add Docker’s official repository
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

apt install docker-ce docker-ce-cli containerd.io docker-compose

systemctl enable docker && sudo systemctl start docker
