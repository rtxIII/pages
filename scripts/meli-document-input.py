import meilisearch
import json
import datetime
"""

"""
DT = datetime.datetime.now().strftime('%Y%m%d')
JSON_FILE = './example.json'
JSON_KEY = 'ID'
MEILI_INDEX = 'example_' + DT
INPUT_BATCH = 10

DISTINCE_ATTRIBUTES = [
    'ID'
]
SEARCHABLE_ATTRIBUTES = [
    'Title',
    'PropertyManufacturer',
    'SellRealName'
]
DISPLAYED_ATTRIBUTES = [
    
]


client = meilisearch.Client('http://localhost:7700', 'aSampleMasterKey')
try:
    client.create_index(MEILI_INDEX, {'primaryKey': JSON_KEY})
except:
    client.update_index(MEILI_INDEX, {'primaryKey': JSON_KEY})

def load_json():
    with open(JSON_FILE, 'r') as f:
        yield json.load(f)

def read_json():
    with open(JSON_FILE, 'r') as f:
        return json.load(f)

def batch_input(batch=INPUT_BATCH):
    _json = read_json()
    _l = len(_json)
    print('Loading total %s itesm' % _l)
    cnt = 0
    for item in _json:
        item.pop('_id')
        print('Loading item %s ' % item)
        cnt += 1
        print(client.index(MEILI_INDEX).add_documents(item, primary_key=JSON_KEY))
        print('Added ' + str(cnt) + ' items')


#client.index(MEILI_INDEX).update('ID')

batch_input()