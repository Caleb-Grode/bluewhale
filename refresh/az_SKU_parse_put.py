import json
import requests
import adal
import boto3

# timeout: 30 seconds (takes about 15)
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
    name_dict = {}
    for v in vm:       
        vm_specs = {}
        vm_specs['name'] = v['name']
        for c in v['capabilities']:
            if c['name'] == 'vCPUs' or c['name'] == 'MemoryGB' or c['name'] == 'ACUs' or c['name'] == 'vCPUsPerCore' or c['name'] == 'MaxResourceVolumeMB' or c['name'] == 'GPUs':
                vm_specs[c['name']] = c['value']
        name_dict[v['name']] = vm_specs

    for key,value in name_dict.items():
        all_vm_specs.append(value)
        
    
    # parse out the specifications of the disks
    name_dict.clear()
    all_disk_specs = []
    for d in disk:
        disk_specs = {}
        disk_specs['name'] = d['name']
        disk_specs['size'] = d['size']
        for c in d['capabilities']:
            disk_specs[c['name']] = c['value']
        name_dict[d['name']] = disk_specs
           
    for ky,val in name_dict.items():
        all_disk_specs.append(val)

    # now we have the data we want!


    print('Number of VMs: ' + str(len(all_vm_specs)))
    print('Number of disks: ' + str(len(all_disk_specs)))


    print("Inputing VMs into DB...")
    # put the data into the database
    azure_vm_table = boto3.resource('dynamodb').Table('bluewhale_vm_3rd_party')
    for item in all_vm_specs:
        azure_vm_table.put_item(Item=item)
    print("Done!")
    
    print("Inputing disks into DB...")
    azure_disk_table = boto3.resource('dynamodb').Table('bluewhale_disk_3rd_party')
    for item in all_disk_specs:
        azure_disk_table.put_item(Item=item)
    print("Done!")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Refresh complete!')
    }
