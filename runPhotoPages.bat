@echo off
echo Running Excel to JSON.py...
python py/Excel_to_JSON.py

echo Running buildPhotoPagesData.js...
node js/buildPhotoPagesData.js

echo ✅ All tasks completed.
pause 