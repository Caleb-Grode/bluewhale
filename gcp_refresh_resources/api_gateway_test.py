import requests
import json

data = requests.get('https://pz9xze9vsl.execute-api.us-east-1.amazonaws.com/prod/virtual-machines/list?provider=Azure&category=general purpose')
j = json.loads(data.text)
for machine in j['Items']:
    print(machine['name'])
    print('...................................')