docker-compose start sentry-postgres sentry-redis

docker-compose run  --rm sentry-base sentry django check

docker-compose run  --rm sentry-base sentry django migrate