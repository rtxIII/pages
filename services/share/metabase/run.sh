docker run -d -p 3000:3000 \
  -e "MB_DB_TYPE=postgres" \
  -e "MB_DB_DBNAME=metabaseappdb" \
  -e "MB_DB_PORT=5432" \
  -e "MB_DB_USER=name" \
  -e "MB_DB_PASS=p0stgr3s" \
  -e "MB_DB_HOST=my-database-host" \
  -e "JAVA_TIMEZONE=Asia/Shanghai"  \
   --name metabase metabase/metabase