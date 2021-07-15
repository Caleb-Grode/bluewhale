potential_matches = [{'MemoryMB':2,'name':1},{'MemoryMB':2,'name':2},{'MemoryMB':3,'name':3},{'MemoryMB':10,'name':4},{'MemoryMB':1,'name':5},{'MemoryMB':5,'name':6}]
vm = {}
vm['MemoryMB'] = 1
matched_instances = []

# we are going to find the 5 closest instances in memory
for i in range(0,5):
    # find the closest instance
    closest = min(potential_matches, key=lambda x:abs(x['MemoryMB']-vm['MemoryMB']))
    # add the instance to our final list
    matched_instances.append(closest)

    print(closest)
    
    # remove the closest from the potential matches so we can find the next closest
    potential_matches = [i for i in potential_matches if not (i['name'] == closest['name'])]

# we now have a list of the five closest instances by memory

