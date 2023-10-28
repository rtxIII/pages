docker run -d --restart=always -v /share/Public/Download/alist:/opt/Download \
              -v /share/Container/apps/alist:/opt/alist/data -p 5244:5244  \
              --name="alist" xhofe/alist:latest

docker run -d --restart=always -v ./data:/opt/alist/data \
           -p 5244:5244 -e PUID=0 -e PGID=0 -e UMASK=022  \
           --name="alist" xhofe/alist:latest


docker exec -it alist ./alist -password

# 随机生成一个密码
docker exec -it alist ./alist admin random
# 手动设置一个密码,`NEW_PASSWORD`是指你需要设置的密码
docker exec -it alist ./alist admin set NEW_PASSWORD