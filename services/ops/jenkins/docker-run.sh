#network
#docker network create jenkins
#export DOCKER_HOST=tcp://127.0.0.1:2376

#run docker master on local
docker run --name jenkins --restart=on-failure --detach \
  --privileged \
  --network host \
  --env JENKINS_JAVA_OPTS=-Dhudson.footerURL=https://jenkins.domain.com \
  --env DOCKER_HOST=tcp://docker:2376 \
  --env DOCKER_CERT_PATH=/certs/client --env DOCKER_TLS_VERIFY=0 \
  --publish 8080:8080 --publish 50000:50000 \
  --volume /srv/jenkins/jenkins_home:/var/jenkins_home \
  --volume /srv/jenkins/certs:/certs/client:ro \
  jenkins/jenkins:lts-jdk17



#run docker agent on local machine
docker run -i --rm --name agent --init jenkins/agent java -jar /usr/share/jenkins/agent.jar -jnlpUrl https://jenkins.domain.com/computer/apple%2Darm%2Dmacmini/jenkins-agent.jnlp -secret 6c52a659fd32bc1fa7bd185e8621d315c399646a6a69b005d900f27600d027db -workDir "/opt/jenkins/agent"

#run docker slave on server
docker run -i --rm  \
             --name agent1 --init -v /srv/jenkins/agent:/home/jenkins/agent rtx3-docker.pkg.coding.net/ops_rtx3/save/jnlp-slave:v2_arm \
              java -jar /usr/share/jenkins/agent.jar -workDir /home/jenkins/agent