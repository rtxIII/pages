 docker exec -t postgres sudo su postgres pg_dump  DATABASE  >  /srv/postgresql/backup/DATABASE_$(date +%F).sql

