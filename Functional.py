import argparse
import json
import os
import sys
import uuid
from uuid import UUID

class ModLoader:
    # File Names/Locations
    gui_order_json = 'game_data.json' # [GUI] List
    load_order_json = 'dlc_load.json' # [Load] List
    registry_json = 'mods_registry.json' # Mod Details
    hash_file = 'dlc_signature' # Resulting Game Hash
    ignore_json = 'ignored_mods.json' # Mods to Ignore (e.g. UI Mods)
    
    # Dictionaries
    mod_lookup = dict() # Used by later lookups to index into database
    mod_dict = dict() # Database of Mod Details
    
    # Output Dictionaries
    _enabled_list = dict()
    _gui_order = dict()
    _ignored_list = dict()
    
    # (Design Intent):
    #    mod_dict (the mod database) tracks mod details and its enabled status
    #    The remaining entities preserve JSON fields and MAY NOT be upto date.
    #        (1) mod_enabled_list    (2) mod_gui_order
    def __init__(this):
        # Read the ignore database
        if(os.path.isfile(this.ignore_json)):
            this._ignored_list = this.import_enabled_list(this.ignore_json)
            
        # Read the Resource Database
        try:
            # Read
            json_file = open(this.registry_json)
            mod_registry = json.load(json_file)       
            json_file.close()
            # Parse
            
            # Take the data of interest, and process it
            for record in mod_registry:          
                keys = set(mod_registry[record].keys())
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
                this.mod_dict[id_int] = {
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
                this.mod_lookup[gameRegistryId] = id_int
                this.mod_lookup[id_str] = id_int
        except:
            print('Error: could not read database.')
        # Read the GUI Presentation Order
        try:
            json_file = open(this.gui_order_json)
            this._gui_order = json.load(json_file)
            json_file.close()
            # Parse the data
            for mod in this._gui_order['modsOrder']:
                id_int = UUID(mod).int # Re-Key the data for direct database use
                mod = id_int # Replace id with integer repersentation
        except:
            print('Error: could not read the mod GUI order.')
        # Read the Enabled Mods List
        try:
            json_file = open(this.load_order_json)
            this._enabled_list = json.load(json_file)
            json_file.close()
            # Parse the data
            for mod in this._enabled_list['enabled_mods']:
                if mod in this.mod_lookup:
                    this.mod_dict[this.mod_lookup[mod]]['enabled'] = True
                else:
                    print('Error: Enabled mod not found in mod database')
        except:
            print('Error: could not read the enabled mods list.')
        # Return the Mod Registry and Mod Order
    
    def disable_mod(this, id_int):
        if id_int in this.mod_dict:
            this._invalidate_hash()
            this.mod_dict[id_int]['enabled'] = False
        else:
            print('Error: Invalid mod specified (Disable Mod).')
    
    def enable_mod(this, id_int):
        if id_int in this.mod_dict:
            this._invalidate_hash()
            this.mod_dict[id_int]['enabled'] = True
        else:
            print('Error: Invalid mod specified (Enable Mod).')
    
    def export_enabled_list(this, fname, order = [], include_ignored = False):
        print('\nExporting Mod List')
        if(not order): # Get current order if none is specified
            order = this.get_uuid_int_list()
        ignored_keys = set(this._ignored_list.keys())
        mod_list = dict()
        for id_int in order:
            # Conditional write based on (Optional) Blacklist
            if(id_int in ignored_keys):
                write = include_ignored
                if(not include_ignored):
                    print('   (Ignored): ' + this.mod_dict[id_int]['displayName'])
            else:
                write = True
            # Export mod if enabled, and allowed by Blacklist filter
            if(this.mod_dict[id_int]['enabled'] and write):
                mod_list[id_int] = {
                        'displayName' : this.mod_dict[id_int]['displayName'],
                        'enabled' : this.mod_dict[id_int]['enabled'],
                        'id' : str(this.mod_dict[id_int]['id']),
                        'steamId' : this.mod_dict[id_int]['steamId']
                    }
        with open(fname, 'w') as outfile:
            json.dump(mod_list, outfile, separators=(',', ':'))
    
    def get_uuid_int_list(this):
        uuid_list = []
        for elem in this._gui_order['modsOrder']:
            uuid_list.append(UUID(elem).int)
        return uuid_list
    
    def import_enabled_list(this, fname):
        new_list = dict()
        json_temp = dict()
        try:
            json_file = open(fname)
            json_temp = json.load(json_file)
            json_file.close()
        except:
            print('Error: could not import the specified list.')
        # Parse Data
        for key in json_temp:
            #print(key)
            id_str = json_temp[key]['id']
            id_int = UUID(id_str).int
            # Reconstruct List using imported records
            new_list[id_int] = {
                'displayName' : json_temp[key]['displayName'],
                'enabled' : json_temp[key]['enabled'],
                'id' : id_str,
                'steamId' : json_temp[key]['steamId']
            }
        return new_list
    
    def enable_import_list(this, fname, include_ignored = False, load_forced = False):
        # Import Enable List
        new_list = this.import_enabled_list(fname)
        # Key Sets
        dict_keys = set( this.get_uuid_int_list() ) # Preserve Existing Order
        import_keys = set( new_list.keys() )
        # Ensure Applicabilitiy
        if(import_keys.issubset(dict_keys) or load_forced):
            # Import is applicable
            ignored_keys = set(this._ignored_list.keys()) # Blacklist
            remaining_order = []
            load_order = [] # Load Ordering
            # Disable Existing Mods
            for key in this.mod_dict:
                # Blacklist Skipping
                if(key in ignored_keys):
                    if(include_ignored):
                        this.mod_dict[key]['enabled'] = False 
                else:
                    this.mod_dict[key]['enabled'] = False
            # Enable Imported Mods
            for key in new_list.keys(): # Preserves Order
                try:
                    # Ternary Test for Removal
                    if(key in ignored_keys):
                        remove = include_ignored
                    else:
                        remove = True
                    # Unconditionally Remove Element:
                    #    a) Pre-Incluced by Blacklist
                    #    b) Included by Import List
                    dict_keys.remove(key) # Raises KeyError if element does not exist
                    if(remove):
                        load_order.append(key) # Preserve the import load order
                        this.mod_dict[key]['enabled'] = True # Enable the mod
                except:
                    print('Error: Imported list of elements in non-uniqe')
            for key in dict_keys: # Move Remaining Elements to the end of list
                if(this.mod_dict[key]['enabled']):
                    remaining_order.append(key) # Black listed mods go to the top
                else:
                    load_order.append(key) # Uninitialized mods go to the bottom
            
            if(remaining_order and load_order):
                remaining_order.extend(load_order)
                return remaining_order 
            elif(load_order):
                return load_order
            else:
                return remaining_order
        else:
            print('Error: Cannot import list, some of the specified mods are missing:')
            Diff = import_keys.difference(dict_keys)
            for key in Diff:
                print('\t(' + new_list[key]['id'] + ' : ' + new_list[key]['displayName'])
            return this.get_uuid_int_list()
    
    def print_list(this, list_order):
        print('\nMod Order:')
        print('---')
        for elem in list_order:
            if elem in this.mod_dict:
                if(this.mod_dict[elem]['enabled']):
                    print('[*] ' + this.mod_dict[elem]['displayName'])
                else:
                    print('[ ] ' + this.mod_dict[elem]['displayName'])
            else:
                print('Error: (Print List) Invalid mod specified.')
    
    def sort_global_list(this, list_order, Rev=True):
        # Construct a Named List for Sorting
        names = []
        for mod_id in list_order:
            try:
                names.append( ((this.mod_dict[mod_id]['displayName'], mod_id)) )
            except:
                print('Error: Append to global sort list ' + str(UUID(int=mod_id)))
        names.sort(key=lambda tup: tup[0], reverse=Rev)
        list_order.clear()
        for elem in names:
            list_order.append(elem[1])
    
    def write_gui_order(this, list_order):
        dict_keys = set(this.mod_dict.keys())
        uuid_str = []
        # Generate the List of UUID Strings
        for int_id in list_order:
            try:
                dict_keys.remove(int_id) # Raises KeyError if element does not exist
                uuid_str.append( str(this.mod_dict[int_id]['id']) )
            except:
                print('Error: (Write GUI Order) Ordered list of elements in non-unique')
        # Catch any elements leaked from original dictionary
        for int_id in dict_keys:
            print('Error: (Write GUI Order) Leaked element: ' + str(int_id))
            uuid_str.append( str(this.mod_dict[int_id]['id']) )
        # Update UUID String
        this._gui_order['modsOrder'] = uuid_str
        # Write out changes
        with open(this.gui_order_json, 'w') as outfile:
            json.dump(this._gui_order, outfile, separators=(',', ':'))
    
    def write_mod_enabled_order(this, list_order, include_ignored = False):
        dict_keys = set(this.mod_dict.keys())
        mod_str = []
        # Generate the List of UUID Strings
        for int_id in list_order:
            try:
                dict_keys.remove(int_id) # Raises KeyError if element does not exist
                if(this.mod_dict[int_id]['enabled']):
                    mod_str.append(this.mod_dict[int_id]['gameRegistryId'])
            except:
                print('Error: (Write mod enabled order) Ordered list of elements in non-unique')
        for int_id in dict_keys:
            if(this.mod_dict[int_id]['enabled']):
                print('Error: (Write mod enabled order) Leaked element: ' + str(UUID(int=mod_id)))
                mod_str.append(this.mod_dict[int_id]['gameRegistryId'])
        # Update Mod String
        this._enabled_list['enabled_mods'] = mod_str
        # Write out changes
        with open(this.load_order_json, 'w') as outfile:
            json.dump(this._enabled_list, outfile, separators=(',', ':'))
            
    def _invalidate_hash(this):
        try:
            os.remove(this.hash_file)
        except:
            pass

## Program Main Loop ##
def main(argv):
    # CLI Argument Parsing
    parser = argparse.ArgumentParser(prog='Mod Launcher',
        description='Mod Launcher (Workaround).')
    parser.add_argument('-if', nargs=1, action='store', dest='infile',
        default='', help='Specify Input Mod List')
    parser.add_argument('-of', nargs=1, action='store', dest='outfile',
        default='', help='Specify Ouput Mod List')
    results = parser.parse_args(argv)

    # Mod Loader Class
    ML = ModLoader()
    
    # Track intermediate ordering as a list of int128's (UUID's)
    temp_order = ML.get_uuid_int_list() # Takes mod_gui_order
    
    # Sort the Mods
    ML.sort_global_list( temp_order, Rev=True )
    
    # Write the enabled list to file
    if(results.outfile):
        ML.export_enabled_list(results.outfile[0])
    
    # Import the enabled list file
    if(results.infile):
        temp_order = ML.enable_import_list(results.infile[0])
    
    # Write the sorted list to console
    ML.print_list(temp_order)
    
    # Write Back the Changes
    ML.write_gui_order(temp_order)
    ML.write_mod_enabled_order(temp_order)

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        main(sys.argv[1:])
    else:
        main('')
