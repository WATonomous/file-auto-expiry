import os
import pwd
import json
import datetime
import time
from ..data.expiry_constants import *
from ..data.tuples import *
from .expiry_checks import is_expired

def get_file_creator(path):
    """
    Returns a tuple including the file creator username, 
    their UID, and GID in that order respectively. 

    string file_path: The absolute path of the file
    """
    # Get the UID of the file or directory owner
    # Get the username associated with the UID
    try:
        username = pwd.getpwuid(os.stat(path).st_uid).pw_name
    except KeyError:
        """ FIX THIS LATER"""
        return f"user{os.stat(path).st_uid}"
    return creator_tuple(username, os.stat(path).st_uid, os.stat(path).st_gid)


def scan_folder_for_expired(folder_path, expiry_threshold, check_folder_atime):
    """Generator function which iterates the expired top level folders
    in a given directory.
    
    Collects expiry information including:
    - all contributing users in the folder
    - the days since the most recent atime, ctime, and mtime of the entire folder
    """
    if not os.path.isdir(folder_path) :
        raise Exception("Given path directory "+ folder_path)

    dirfd = os.open(folder_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOATIME)
    for entry in os.scandir(dirfd):
        entry_path = os.path.join(folder_path, entry.path)
        if os.path.exists(entry_path):
            expiry_result = is_expired(entry_path, expiry_threshold, check_folder_atime)
            # path, creator tuple (name, uid, gid), atime, ctime, mtime
            yield entry_path, expiry_result.is_expired, expiry_result.creators, \
                expiry_result.atime, expiry_result.ctime, expiry_result.mtime, expiry_result.size
    os.close(dirfd)

def collect_expired_file_information(folder_path, save_file, scrape_time, expiry_threshold, check_folder_atime, overwrite_file=True):
    """
    Interface function which collects which directories are 'expired'

    String folder_path: The folder to scan for expired files
    String save_file: The jsonl file path to save the information to, 
    ie "path_name.jsonl"
    Int scrape_time: the time at the start of the information scrape
    Int seconds_for_expiry: The amount of days since last usage that indicates 
    expiry
    """
    if not os.path.isdir(folder_path):
        raise Exception("Base folder does not exist")
    
    if not save_file:
        # save_file path not given
        save_file = f"file_information_{str(datetime.datetime.fromtimestamp(scrape_time))}.jsonl"

    path_info = dict()
    for path, is_expired, creators, atime, ctime, mtime, size in scan_folder_for_expired(
        folder_path, expiry_threshold, check_folder_atime):
        # handles generating the dictionary
        recent_time =  max(datetime.datetime.fromtimestamp(atime), datetime.datetime.fromtimestamp(ctime));
        recent_time = max(recent_time, datetime.datetime.fromtimestamp(mtime))
        days_unused = (datetime.datetime.now() - recent_time).days
        path_info[path] = { 
            "path": path, # storing pathname so we keep it when we transfer the dictionary to jsonl
            "creators": [creator for creator in creators if isinstance(creator[1], int) and creator[1] > 0 and creator[1] == creator[2]],
            "expired": is_expired,
            "folder_stats": {
                "atime_datetime": str(datetime.datetime.fromtimestamp(atime)),
                "ctime_datetime": str(datetime.datetime.fromtimestamp(ctime)),
                "mtime_datetime": str(datetime.datetime.fromtimestamp(mtime)),
                "days_unused": days_unused,
                "size_bytes": size,
                "size_mb": size / BYTES_PER_MB
            }}        
    
    write_jsonl_information(path_info, save_file, scrape_time, expiry_threshold, overwrite_file=overwrite_file)

def write_jsonl_information(dict_info, file_path, scrape_time, expiry_threshold="", overwrite_file=True):
    current_time = time.time()
    mode = "w" if overwrite_file else "a+"
    with open(file_path, mode) as file:
        if (overwrite_file):
            if expiry_threshold=="":
                file.write(json.dumps({"scrape_time:": scrape_time,
                                "scrape_time_datetime": str(datetime.datetime.fromtimestamp(scrape_time))}) + "\n")
            else:
                file.write(json.dumps({"scrape_time:": scrape_time,
                                "scrape_time_datetime": str(datetime.datetime.fromtimestamp(scrape_time)),
                                "expiry_threshold": str(datetime.datetime.fromtimestamp(expiry_threshold))}) + "\n")
            file.write(json.dumps({"time_for_scrape_sec": current_time - scrape_time,
                                "time_for_scrape_min": (current_time - scrape_time) / 60}) + "\n")
            
        for key in dict_info:
            file.write(json.dumps(dict_info[key]) + "\n") 

def collect_creator_information(path_info_file, save_file, scrape_time, overwrite_file=True):
    """
    Returns a dictionary relating path information to each creator
    Must be given the return value of form similar to the output of 
    collect_expired_file_information()

    String path_info_file: A jsonl file path containing information about a 
    certain path. This should be the result of calling the collect_file_information
    function.

    String save_file: The jsonl file path to save the information to, 
    ie "path_name.jsonl"

    Int scrape_time: The time at the start of the information scrape. 
    """
    if not os.path.exists(path_info_file):
        raise Exception("Given file for path information does not exist")

    if not save_file:
        # save_file path not given
        save_file = f"creator_information_{str(datetime.datetime.fromtimestamp(scrape_time))}.jsonl"

    creator_info = dict()
    with open(path_info_file, "r+") as file:
        lines = file.readlines()

    for line in lines[2:]:
            # One jsonl line of path inforamtion
            path_data = json.loads(line)
            # check if the path is expired
            if path_data["expired"]:
                # take all unique creators and make a new dictionary about them
                for user in path_data["creators"]:
                    stats = path_data["folder_stats"]
                    if user[1] in creator_info:
                        creator_info[user[1]]["paths"][path_data["path"]] = stats
                        
                    else:
                        if isinstance(user[1], int):
                            creator_info[user[1]] = {
                            "paths": {path_data["path"]: stats}, 
                            "name": user[0],
                            "uid": user[1],
                            "gid": user[2]}
    write_jsonl_information(creator_info, save_file, scrape_time, overwrite_file=overwrite_file)