docker build -t myjenkins-blueocean:2.414.2-1 .


docker build --platform=linux/amd64  -f Dockerfile-Slave -t rtx3-docker.pkg.coding.net/ops_rtx3/save/jnlp-slave:v3_arm .
docker push rtx3-docker.pkg.coding.net/ops_rtx3/save/jnlp-slave:v3_arm

docker buildx build --platform=linux/amd64  -f Dockerfile-Slave -t rtx3-docker.pkg.coding.net/ops_rtx3/save/jnlp-slave:v3_linux .
docker push rtx3-docker.pkg.coding.net/ops_rtx3/save/jnlp-slave:v3_linux