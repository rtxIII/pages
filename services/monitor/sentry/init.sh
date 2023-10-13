docker-compose start sentry-postgres sentry-redis

docker-compose run  --rm sentry-base --config=/conf/sentry_docker_conf.py  django check

docker-compose run  --rm sentry-base --config=/conf/sentry_docker_conf.py  django migrate