import requests
import adal
import json

# call azure API!

azure_client_id = '6d982d3d-8d28-4e03-abe2-b4dda6ae7ad4'
azure_secret = 'Fk1VKt7.Tyiz-iq2CIW_~tUY5kg5w9Nc8a'
azure_subscription_id = 'ccd88d99-7410-4b16-a568-e76803014994'
azure_tenant = 'd194cd5c-f1f0-453d-bd4b-df49d6ac9d48'
authority_url = 'https://login.microsoftonline.com/' + azure_tenant
resource = 'https://management.azure.com/'

context = adal.AuthenticationContext(authority_url)
token = context.acquire_token_with_client_credentials(resource, azure_client_id, azure_secret)

headers = {'Authorization': 'Bearer ' + token['accessToken'], 'Content-Type': 'application/json'}

params = {'api-version': '019-04-01'}
url = 'https://management.azure.com/subscriptions/'+azure_subscription_id+'/providers/Microsoft.Compute/skus'

r = requests.get(url, headers=headers, params=params)

print(json.dumps(r.json(), indent=4, separators=(',', ': ')))

