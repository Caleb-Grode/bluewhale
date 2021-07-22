import requests
import adal
import json
import os

# call azure API!

# info for azure authentification
azure_client_id = os.environ['azure_client_id']
azure_secret = os.environ['azure_secret']
azure_subscription_id = os.environ['azure_subscription_id']
azure_tenant = os.environ['azure_tenant']
authority_url = 'https://login.microsoftonline.com/' + azure_tenant
resource = 'https://management.azure.com/'

context = adal.AuthenticationContext(authority_url)
token = context.acquire_token_with_client_credentials(resource, azure_client_id, azure_secret)

headers = {'Authorization': 'Bearer ' + token['accessToken'], 'Content-Type': 'application/json'}

params = {'api-version': '019-04-01'}
url = 'https://management.azure.com/subscriptions/'+azure_subscription_id+'/providers/Microsoft.Compute/skus'

r = requests.get(url, headers=headers, params=params)

print(json.dumps(r.json(), indent=4, separators=(',', ': ')))

