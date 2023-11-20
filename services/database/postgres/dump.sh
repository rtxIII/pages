 docker exec -t postgres pg_dump -U postgres  DATABASE  >  /srv/postgresql/backup/DATABASE_$(date +%F).sql

