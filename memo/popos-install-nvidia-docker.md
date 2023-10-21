It seems a problem was introduced with Pop OS 21.04 but to resolve this problem you need to follow these steps :

distribution=ubuntu22.04 && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo nano /etc/apt/preferences.d/pop-default-settings and then add
Package: *
Pin: origin nvidia.github.io
Pin-Priority: 1002
in order to give nvidia's repositories higher pin priorities
sudo apt update
sudo apt install nvidia-docker2 → this will install all the dependencies
sudo systemctl restart docker
Now sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi should work.