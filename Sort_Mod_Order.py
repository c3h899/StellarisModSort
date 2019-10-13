import json
import os
import uuid
from uuid import UUID

mod_gui_order_json = 'game_data.json' # [GUI] List
mod_order_json = 'dlc_load.json' # [Load] List
mod_registry_json = 'mods_registry.json' # Mod Details
mod_hash = 'dlc_signature' # Resulting Game Hash

# Load the Mod Database (*NOT* Where order is asserted)
name_lookup = dict()
with open(mod_registry_json) as json_file:
    mod_registry = json.load(json_file)
    # Dump the interal file name and print text for lookup
    for record in mod_registry:
        key = mod_registry[record]['gameRegistryId']
        mod_id = mod_registry[record]['id'] # Same as record
        mod_registry[record]['id'] = UUID(mod_id).bytes
        value = mod_registry[record]['displayName']
        name_lookup[key] = value # Used by [Load] List
        name_lookup[mod_id] = value # Used by [GUI] List

if(name_lookup):
    # Mod Presentation Order ( as in GUI/Paradox Launcher )
    all_mods = []
    with open(mod_gui_order_json) as json_file:
        mod_gui_order = json.load(json_file)
        
        # Make a backup copy of the object
        with open(mod_gui_order_json + '.bak', 'w') as outfile:
            json.dump(mod_gui_order, outfile, separators=(',', ':'))
            
        for mod_id in mod_gui_order['modsOrder']:
            all_mods.append( ((name_lookup[mod_id], mod_id)) )
        
    # Sort and Write Back the File
    if(all_mods):
        all_mods.sort(key=lambda tup: tup[0], reverse=True)
        mod_gui_order['modsOrder'] = [ elem[1] for elem in all_mods ]
        
        # Write the Sorted output to the original file
        with open(mod_gui_order_json, 'w') as outfile:
            json.dump(mod_gui_order, outfile, separators=(",", ":"))

    # Load the Mod Ordering File (Where order is asserted)
    enabled_mods = []
    with open(mod_order_json) as json_file:
        mod_order = json.load(json_file)

        # Make a backup copy of the object
        with open(mod_order_json + '.bak', 'w') as outfile:
            json.dump(mod_order, outfile, separators=(',', ':'))

        # Dump the Enabled Mods and their corresponding names as tuples
        for mod_file in mod_order['enabled_mods']:
            enabled_mods.append( ((name_lookup[mod_file], mod_file)) )

    # Sort and Write Back the File
    if(enabled_mods):
        # Invalidate Existing Mod Hash
        try:
            os.remove(mod_hash)
        except:
            print('No previously existing mod hash found.\n')

        # Sort the [Load] List by Name
        enabled_mods.sort(key=lambda tup: tup[0], reverse=True)
        mod_order['enabled_mods'] = [ elem[1] for elem in enabled_mods ]
    
        # Print the Sorted [Load] List to Consol:
        print('[Output Mod Order]\n')
        for key in mod_order['enabled_mods']:
            print(name_lookup[key])
    
        # Write the Sorted output to the original file
        with open(mod_order_json, 'w') as outfile:
            json.dump(mod_order, outfile, separators=(",", ":"))

else:
    print('No Mods Enabled')