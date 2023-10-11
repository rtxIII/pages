#docker pull postgres:14-bullseye
docker run -d \
	--name postgres \
    -p 5432:5432 \
    -e POSTGRES_USER=postgres \
	-e POSTGRES_PASSWORD=p0stgr3s \
	-e PGDATA=/var/lib/postgresql/data/pgdata \
    -e TZ=Asia/Shanghai \
	-v /srv/postgresql/data:/var/lib/postgresql/data \
	postgres:14-bullseye