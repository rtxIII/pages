#create org
docker-compose  exec zulip su zulip -c '/home/zulip/deployments/2023-11-04-14-38-23/manage.py generate_realm_creation_link'
#register server for mobile push
docker-compose  exec zulip su zulip -c '/home/zulip/deployments/current/manage.py register_server'
#restart server
docker-compose  exec zulip su zulip -c '/home/zulip/deployments/current/scripts/restart-server'