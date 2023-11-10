# Fetch the latest version of MeiliSearch image from DockerHub
docker pull getmeili/meilisearch:latest

# Launch MeiliSearch
#docker run -it --rm \
#    -p 7700:7700 \
#    -v /data/meili/data.ms:/data.ms \
#    getmeili/meilisearch:latest

docker run \
    -p 7700:7700 \
    -v /data/meili/data.ms:/data.ms \
    -d \
    getmeili/meilisearch:latest