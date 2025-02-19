#/Users/mac/Zero/Proj/Coding/nodevops
#hugo
#1 生成nav
python nav.py >  ./layouts/partials/nav.html
#2 生成md
hugo 
#3 同步
rsync --exclude-from=./exclude.txt  -avz  /Users/mac/Zero/Proj/Coding/nodevops/page/src/public/  /Users/mac/Zero/Proj/Coding/nodevops/docs/
#4 发布
cd /Users/mac/Zero/Proj/Coding/nodevops/docs/ 
git add .
git commit -m "update docs by hugo Date: `date +%Y-%m-%d`"
git push origin main