#JSON only
mongoexport --host=127.0.0.1 --port=27017 -d rex -c CARDHOBBY.CARD --jsonArray -o card.json
#JSON without _id
mongoexport --host=127.0.0.1 --port=27017 -d rex -c CARDHOBBY.CARD --jsonArray | sed '/"_id":/s/"_id":[^,]*,//' > users.json