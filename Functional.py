import json
import os
import uuid
from uuid import UUID

mod_gui_order_json = 'game_data.json' # [GUI] List
mod_order_json = 'dlc_load.json' # [Load] List
mod_registry_json = 'mods_registry.json' # Mod Details
mod_hash = 'dlc_signature' # Resulting Game Hash

# (Design Intent):
#    mod_dict (the mod database) tracks mod details and its enabled status
#    The remaining entities preserve JSON fields and MAY NOT be upto date.
#        (1) mod_enabled_list    (2) mod_gui_order
def read_mod_data():
    # Read the Resource Database
    try:
        # Read
        json_file = open(mod_registry_json)
        mod_registry = json.load(json_file)       
        json_file.close()
        # Parse
        mod_dict = dict()
        mod_lookup = dict() # Used by later lookups to index into database
        # Take the data of interest, and process it
        for record in mod_registry:          
            keys = mod_registry[record].keys()
            # Sanatize inputs, provide defaults in not specified
            if 'id' in keys:
                id_str = mod_registry[record]['id']
                id_uuid = UUID(id_str) 
                id_int = id_uuid.int
            else:
                print('Error: Mod database entry has no ID')
            if 'gameRegistryId' in keys:
                gameRegistryId = mod_registry[record]['gameRegistryId']
            else:
                print('Error: Mod database entry has no gameregistryId')    
            if 'displayName' in keys:
                displayName = mod_registry[record]['displayName']
            else:
                displayName = 'Unnammed Mod'
            if 'requiredVersion' in keys:
                requiredVersion = mod_registry[record]['requiredVersion']
            else:
                requiredVersion = '0.0.0'
            if 'source' in keys:
                source = mod_registry[record]['source']
            else:
                source = 'none'
            if 'status' in keys:
                status = mod_registry[record]['status']
            else:
                status = 'undefined'
            if 'steamId' in keys:
                steamId = int(mod_registry[record]['steamId'])
            else:
                steamId = int(0)
            if 'tags' in keys:
                tags = mod_registry[record]['tags']
            else:
                tags = ['']
            if 'thumbnailPath' in keys:
                thumbnailPath = mod_registry[record]['thumbnailPath']
            else:
                thumbnailPath = ''
            if 'thumbnailUrl' in keys:
                thumbnailUrl = mod_registry[record]['thumbnailUrl']
            else:
                thumbnailUrl = ''
            if 'timeUpdated' in keys:
                timeUpdated = int(mod_registry[record]['timeUpdated'])
            else:
                timeUpdated = int(0)
            # Record Sanitized Dictionary
            mod_dict[id_int] = {
                'displayName' : displayName,
                'enabled' : False,
                'gameRegistryId' : gameRegistryId,
                'id' : id_uuid, # Pythonic UUID Object
                'requiredVersion' : requiredVersion,
                'source' : source,
                'status' : status,
                'steamId' : steamId,
                'tags' : tags,
                'thumbnailPath' : thumbnailPath,
                'thumbnailUrl' : thumbnailUrl,
                'timeUpdated' : timeUpdated
            }
            mod_lookup[gameRegistryId] = id_int
            mod_lookup[id_str] = id_int
    except:
        print('Error: could not read database.')
    # Read the GUI Presentation Order
    try:
        json_file = open(mod_gui_order_json)
        mod_gui_order = json.load(json_file)
        json_file.close()
        # Parse the data
        for mod in mod_gui_order['modsOrder']:
            id_int = UUID(mod).int # Re-Key the data for direct database use
            mod = id_int # Replace id with integer repersentation
    except:
        print('Error: could not read the mod GUI order.')
    # Read the Enabled Mods List
    try:
        json_file = open(mod_order_json)
        mod_enabled_list = json.load(json_file)
        json_file.close()
        # Parse the data
        for mod in mod_enabled_list['enabled_mods']:
            if mod in mod_lookup:
                mod_dict[mod_lookup[mod]]['enabled'] = True
            else:
                print('Error: Enabled mod not found in mod database')
    except:
        print('Error: could not read the enabled mods list.')
    # Return the Mod Registry and Mod Order
    return [mod_dict, mod_enabled_list, mod_gui_order]

def invalidate_hash():
    try:
        os.remove(mod_hash)
    except:
        pass

def disable_mod(id_int, mod_dict):
    if id_int in mod_dict:
        invalidate_hash()
        mod_dict[id_int]['enabled'] = False
    else:
        print('Error: Invalid mod specified (Disable Mod).')

def enable_mod(id_int, mod_dict):
    if id_int in mod_dict:
        invalidate_hash()
        mod_dict[id_int]['enabled'] = True
    else:
        print('Error: Invalid mod specified (Enable Mod).')

def get_uuid_int_list(mod_gui_order):
    uuid_list = []
    for elem in mod_gui_order['modsOrder']:
        uuid_list.append(UUID(elem).int)
    return uuid_list

def print_list(list_order, mod_dict):
    print('Mod Order:')
    print('---')
    for elem in list_order:
        if elem in mod_dict:
            if(mod_dict[elem]['enabled']):
                print('[*] ' + mod_dict[elem]['displayName'])
            else:
                print('[ ] ' + mod_dict[elem]['displayName'])
        else:
            print('Error: (Print List) Invalid mod specified.')

def sort_global_list(list_order, mod_dict, Rev=True):
    # Construct a Named List for Sorting
    names = []
    for mod_id in list_order:
        names.append( ((mod_dict[mod_id]['displayName'], mod_id)) )
    names.sort(key=lambda tup: tup[0], reverse=Rev)
    list_order.clear()
    for elem in names:
        list_order.append(elem[1])

def write_gui_order(list_order, mod_gui_order, mod_dict):
    dict_keys = set(mod_dict.keys())
    uuid_str = []
    # Generate the List of UUID Strings
    for int_id in list_order:
        try:
            dict_keys.remove(int_id) # Raises KeyError if element does not exist
            uuid_str.append( str(mod_dict[int_id]['id']) )
        except:
            print('Error: (Write GUI Order) Ordered list of elements in non-uniqe')
    # Catch any elements leaked from original dictionary
    for int_id in dict_keys:
        print('Error: (Write GUI Order) Leaked element: ' + int_id)
        uuid_str.append( str(mod_dict[int_id]['id']) )
    # Update UUID String
    mod_gui_order['modsOrder'] = uuid_str
    # Write out changes
    with open(mod_gui_order_json, 'w') as outfile:
        json.dump(mod_gui_order, outfile, separators=(',', ':'))

def write_mod_enabled_order(list_order, mod_enabled_list, mod_gui_order, mod_dict):
    dict_keys = set(mod_dict.keys())
    mod_str = []
    # Generate the List of UUID Strings
    for int_id in list_order:
        try:
            dict_keys.remove(int_id) # Raises KeyError if element does not exist
            if(mod_dict[int_id]['enabled']):
                mod_str.append(mod_dict[int_id]['gameRegistryId'])
        except:
            print('Error: (Write mod enabled order) Ordered list of elements in non-uniqe')
    for int_id in dict_keys:
        if(mod_dict[int_id]['enabled']):
            print('Error: (Write mod enabled order) Leaked element: ' + int_id)
            mod_str.append(mod_dict[int_id]['gameRegistryId'])
    # Update Mod String
    mod_enabled_list['enabled_mods'] = mod_str
    # Write out changes
    with open(mod_order_json, 'w') as outfile:
        json.dump(mod_enabled_list, outfile, separators=(',', ':'))

## Program Main Loop ##

# Read the source files
mod_lists = read_mod_data()
    # List[0] is the Working Dictionary
    # List[1] is mod_enabled_list
    # List[2] is mod_gui_order

# Track intermediate ordering as a list of int128's (UUID's)
temp_order = get_uuid_int_list( mod_lists[2] ) # Takes mod_gui_order

# Sort the Mods
sort_global_list( temp_order, mod_lists[0], Rev=True )

# Write the sorted list to console
print_list(temp_order, mod_lists[0])

# Write Back the Changes
write_gui_order( temp_order, mod_lists[2], mod_lists[0] )
write_mod_enabled_order( temp_order, mod_lists[1], mod_lists[2], mod_lists[0] )
