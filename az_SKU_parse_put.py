import json
import requests
import adal
import boto3

# timeout: 15 seconds (takes about 4)
# memory: 512MB (uses about 251)

def lambda_handler(event, context):

    # info for azure authentification
    azure_client_id = '445dd70f-6e05-4b46-b9c6-70a2f76f74a3'
    azure_secret = '2zSQ1B_fSWfgj_~7HcEzBO9rob0-IVVSXx'
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
    
    
    print("calling API")
    azure_SKUs_JSON = requests.get(url, headers=headers, params=params)
    print("API called!")
    azure_SKUs_JSON = azure_SKUs_JSON.json()

    
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
    azure_vm_table = boto3.resource('dynamodb').Table('bluewhale_vm_3rd_party')
    for item in all_vm_specs:
        azure_vm_table.put_item(Item=item)
    
    azure_disk_table = boto3.resource('dynamodb').Table('bluewhale_disk_3rd_party')
    for item in all_disk_specs:
        azure_disk_table.put_item(Item=item)


    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
