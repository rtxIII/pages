#network
#docker network create jenkins
#export DOCKER_HOST=tcp://127.0.0.1:2376

docker run --name jenkins --restart=on-failure --detach \
  --privileged \
  --network host \
  --env JENKINS_JAVA_OPTS=-Dhudson.footerURL=https://jenkins.we2.xyz \
  --env DOCKER_HOST=tcp://docker:2376 \
  --env DOCKER_CERT_PATH=/certs/client --env DOCKER_TLS_VERIFY=0 \
  --publish 8080:8080 --publish 50000:50000 \
  --volume /srv/jenkins/jenkins_home:/var/jenkins_home \
  --volume /srv/jenkins/certs:/certs/client:ro \
  jenkins/jenkins:lts-jdk17

  c74d3a07198245e994b1fc2f88cda72e



docker run -i --rm  \
             --name agent1 --init -v /srv/jenkins/agent:/home/jenkins/agent rtx3-docker.pkg.coding.net/ops_rtx3/save/jnlp-slave:v2_arm \
              java -jar /usr/share/jenkins/agent.jar -workDir /home/jenkins/agent