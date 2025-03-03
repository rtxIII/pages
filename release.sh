#3 同步
rsync --exclude-from=./exclude.txt  -avz  ./page/src/public/  ./docs/
#4 发布
cd ./docs/ 
git add .
git commit -m "update docs by hugo Date: `date +%Y-%m-%d`"
git push origin main