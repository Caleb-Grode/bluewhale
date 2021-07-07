import requests
import adal
import boto3

# Calls Azure API, parses data, puts into database

# info for azure authentification
azure_client_id = '6d982d3d-8d28-4e03-abe2-b4dda6ae7ad4'
azure_secret = 'Fk1VKt7.Tyiz-iq2CIW_~tUY5kg5w9Nc8a'
azure_subscription_id = 'ccd88d99-7410-4b16-a568-e76803014994'
azure_tenant = 'd194cd5c-f1f0-453d-bd4b-df49d6ac9d48'
authority_url = 'https://login.microsoftonline.com/' + azure_tenant
resource = 'https://management.azure.com/'

# for API request
context = adal.AuthenticationContext(authority_url)
token = context.acquire_token_with_client_credentials(resource, azure_client_id, azure_secret)

# API request header
headers = {'Authorization': 'Bearer ' + token['accessToken'], 'Content-Type': 'application/json'}

# API params and url
params = {'api-version': '019-04-01'}
url = 'https://management.azure.com/subscriptions/'+azure_subscription_id+'/providers/Microsoft.Compute/skus'

azure_SKUs_JSON = requests.get(url, headers=headers, params=params).json()

# now we have our Azure data
# begin parsing

vm = []
disk = []
for j in azure_SKUs_JSON['value']:
        # grab all VMs
    if j['resourceType'] == 'virtualMachines':
        vm.append(
            j
        )
    # grab all disks
    elif j['resourceType'] == 'disks':
        disk.append(
            j
        )


# parse out the specifications of the VMs
all_vm_specs = []
for v in vm:
    vm_specs = {}
    vm_specs['name'] = v['name']
    for c in v['capabilities']:
        if c['name'] == 'vCPUs' or c['name'] == 'MemoryGB' or c['name'] == 'vCPUsAvailable' or c['name'] == 'ACUs' or c['name'] == 'vCPUsPerCore':
            vm_specs[c['name']] = c['value']
    all_vm_specs.append(vm_specs)

# parse out the specifications of the disks
all_disk_specs = []
for d in disk:
    disk_specs = {}
    disk_specs['name'] = v['name']
    disk_specs['size'] = v['size']
    for c in d['capabilities']:
        disk_specs[c['name']] = c['value']
    all_disk_specs.append(disk_specs)

# now we have the data we want!

# put the data into the database
client = boto3.client('dynamodb')


azure_vm_table = client.table('bluewhale_vm_3rd_party')
response = azure_vm_table.batch_write_item(RequestItems=all_vm_specs)

azure_disk_table = client.table('bluewhale_disk_3rd_party')
response = azure_disk_table.batch_write_item(RequestItems=all_disk_specs)





