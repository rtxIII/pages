docker exec -i postgres psql -U postgres < schema/db.sql

psql -c 'DROP DATABASE <your_db_name>'