#docker pull postgres:14-bullseye
docker run -d \
	--name redis \
    -p 6379:6379 \
    -e TZ=Asia/Shanghai \
	-v /srv/redis/data:/data \
	redis:5.0-alpine