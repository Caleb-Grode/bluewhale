import json

# parse list-sku azure api calls

with open('list-skus.json') as json_file:
    data = json.load(json_file)

vm = []
disk = []
for j in data:
    if j['resourceType'] == 'virtualMachines':
        vm.append(
            j
        )
    elif j['resourceType'] == 'disks':
        disk.append(
            j
        )


all_vm_specs = []
for v in vm:
    vm_specs = {}
    vm_specs['name'] = v['name']
    for c in v['capabilities']:
        if c['name'] == 'vCPUs' or c['name'] == 'MemoryGB' or c['name'] == 'vCPUsAvailable' or c['name'] == 'ACUs' or c['name'] == 'vCPUsPerCore':
            vm_specs[c['name']] = c['value']
    all_vm_specs.append(vm_specs)

all_disk_specs = []
for d in disk:
    disk_specs = {}
    disk_specs['name'] = v['name']
    disk_specs['size'] = v['size']
    for c in d['capabilities']:
        disk_specs[c['name']] = c['value']
    all_disk_specs.append(disk_specs)

for dict in all_vm_specs:
    print(dict)
    print()

#for dict in all_disk_specs:
#    print(dict)
#    print()
    
