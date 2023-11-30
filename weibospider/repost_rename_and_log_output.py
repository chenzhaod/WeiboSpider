# Updated at 2023-11-15

# This script:
# (1) rename the output from feedback tracking to "time_group range"
# (2) create/maintain a "repost_output_log.json" file to log the tracking process
# (3) create/maintain a "repost_group_tracking_status.json" file to log the current tracking status of each group
# (4) create/maintain a "repost_error_log" file to log the failed cases of repost tracking

import os
import datetime
import json
import dropbox

def read_file_from_dropbox(dbx, file_path):
    """
    Reads a file's contents from Dropbox.
    :param dbx: Dropbox's client instance
    :param file_path: path of the file in Dropbox
    :return: Returns the file's contents as a string, or None if an error occurs
    """
    try:
        # Attempt to download the file from Dropbox
        _, res = dbx.files_download(file_path)
        # Decode the file content to string
        return res.content.decode('utf-8')
    except dropbox.exceptions.ApiError as e:
        print(f"Error reading file from Dropbox: {file_path}")
        return None

def write_file_to_dropbox(dbx, file_path, content):
    """
    Writes content to a file in Dropbox.
    :param dbx: Dropbox client instance.
    :param file_path: Path of the file in Dropbox.
    :param content: Content to be written to the file
    """
    try:
        # Upload the content to the specified Dropbox file path
        dbx.files_upload(content.encode('utf-8'), file_path, mode=dropbox.files.WriteMode("overwrite"))
    except dropbox.exceptions.ApiError as e:
        print(f"Error writing file to Dropbox: {file_path}")

def upload_file_to_dropbox(dbx, local_file_path, dropbox_file_path):
    """
    Uploads a file from the local file system to Dropbox.
    :param dbx: Dropbox client instance.
    :param local_file_path: Directory in the GitHub Actions runner.
    :param dropbox_file_path: Directory in Dropbox
    :return:
    """
    with open(local_file_path, 'rb') as f:
        dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))

def rename_output_file(dbx,
                       group_range_file="/Dissertation/weibo_data/records_and_logs/group_number_range.txt",
                       local_output_dir="../output/",
                       dropbox_output_dir="/Dissertation/weibo_data/repost_output/",
                       error_log_file="/Dissertation/weibo_data/records_and_logs/repost_error_log.json"):
    """
    Looks for the latest file in a local directory, renames it, and uploads it to Dropbox.
    Also reads the group number range from Dropbox and incorporates it into the new file name.
    If no file is found or an error occurs, logs the error and returns False.
    :param dbx: Dropbox client instance.
    :param group_range_file: Path to read the group number range from Dropbox
    :param local_output_dir: Path to local output file
    :param dropbox_output_dir: Path to Dropbox where the output file should be uploaded
    :param error_log_file: Path to error log file
    :return: (1) renamed output file uploaded to Dropbox (2) the new file name (3) updated error log file, if an error occurs
    """

    # Get the current time in the desired format
    creation_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Try to read the group number range from Dropbox
    group_range_content = read_file_from_dropbox(dbx, group_range_file)
    if group_range_content is None:
        print("Group range file not found in Dropbox")
        return None, False

    # Split the content into lines to extract group numbers
    group_numbers = group_range_content.splitlines()

    # Extract the first and last group numbers from the list
    first_group = group_numbers[0].strip()
    last_group = group_numbers[-1].strip()

    # Format the new file name
    new_file_name = f"{creation_time}_group_{first_group}_group_{last_group}.jsonl"

    # Initialize a flag to track whether any file has been found and renamed
    found_file = False

    # Search for a file to rename in the local output directory
    for filename in os.listdir(local_output_dir):
        if filename.endswith('.jsonl'): # replace with file extension
            local_original_file_path = os.path.join(local_output_dir, filename) # construct the full path to the original file
            local_new_file_path = os.path.join(local_output_dir, new_file_name) # construct the full path to new file
            dropbox_new_file_path = os.path.join(dropbox_output_dir, new_file_name) # construct the full path to Dropbox

            # rename the file locally, moving it from the original path to the new path with the new file name
            os.rename(local_original_file_path, local_new_file_path)
            print(f"Data file {filename} has been renamed to: {new_file_name}")

            # upload the renamed file to Dropbox
            upload_file_to_dropbox(dbx, local_new_file_path, dropbox_new_file_path)
            print(f"Data file {new_file_name} has been uploaded to Dropbox")
            found_file = True # flag to True
            break
            # NOTE: The current function assumes only one file needs to be renamed

    # return none if no file was named
    if not found_file:
        # construct an error message and log the error
        error_message = f"No output file found for group {first_group} to group {last_group} at {creation_time}"
        log_error(dbx, error_message, error_log_file)
        print(error_message)
        return None, False # return None and a False success flag

    return new_file_name, True

def log(dbx,
        new_file_name,
        group_range_file="/Dissertation/weibo_data/records_and_logs/group_number_range.txt",
        tracking_log_file="/Dissertation/weibo_data/records_and_logs/repost_output_log.json",
        group_status_log_file="/Dissertation/weibo_data/records_and_logs/repost_group_tracking_status.json"):
    """
    Logs the tracking details and status
    :param dbx: Dropbox client instance
    :param new_file_name: the new file name returned from "rename_output_file" function
    :param group_range_file: path to group number range file
    :param tracking_log_file: path to repost_output_log.json
    :param group_status_log_file: path to repost_group_tracking_status.json
    :return: updated repost_output_log and repost_group_tracking_status.json
    """

    # the timestamp that will be used in the tracking record
    creation_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Read group range content from Dropbox
    group_range_content = read_file_from_dropbox(dbx, group_range_file)
    # If the file is not found in Dropbox, print a message and exit the function
    if group_range_content is None:
       print("Group range file not found in Dropbox")
       return

    # Split the group range content into lines (group numbers
    group_numbers = group_range_content.splitlines()

    # calls the 'record_tracking' function to log the details of tracking
    record_tracking(dbx, new_file_name, creation_time, group_numbers, tracking_log_file, success)

    # for each group number, calls the 'record_group_tracking_status' function
    for group_number in group_numbers:
        record_group_tracking_status(dbx, int(group_number), group_status_log_file) # group number converted to integer

def record_tracking(dbx, filename, creation_time, group_numbers, tracking_log_file, success):
    """
    Records each repost tracking in a JSON file
    :param dbx: Dropbox client instance
    :param filename: the output file name
    :param creation_time: creation time of the file
    :param group_numbers: the file's group number
    :param tracking_log_file: the log file
    :param success: whether the tracking was success or not
    :return: updated repost_output_log file 
    """
    # create a dictionary that holds the tracking information
    tracking_data = {
        "filename": filename,
        "creation_time": creation_time,
        "groups_in_it": ", ".join(group_numbers),
        "success": success
    }

    # Read existing tracking data from Dropbox
    content = read_file_from_dropbox(dbx, tracking_log_file)
    # Load it as JSON if available, else start with an empty list
    data = json.loads(content) if content else []

    # Append the new tracking data
    data.append(tracking_data)
    # Convert the updated list to a JSON string
    new_content = json.dumps(data, indent=4)
    # Write the updated tracking data back to Dropbox
    write_file_to_dropbox(dbx, tracking_log_file, new_content)

def record_group_tracking_status(dbx,
                                 group_number,
                                 tracking_status_file="/Dissertation/weibo_data/records_and_logs/repost_group_tracking_status.json"):
    """
    Records the tracking status of each group.
    :param dbx: Dropbox client instance
    :param group_number: the group number of the current data group
    :param tracking_status_file: path to the repost_group_tracking_status.json file
    :return: updated repost_group_tracking_status.json
    """
    # calls the get_original_creation_time function to return the original creation time of each group
    original_creation_time = get_original_creation_time(dbx, group_number)

    # Read existing group tracking status from Dropbox
    content = read_file_from_dropbox(dbx, tracking_status_file)
    # Load it as JSON, else start with an empty list
    tracking_status = json.loads(content) if content else []

    # search existing entry in 'tracking_status' that matches the current group number
    group_entry = next((entry for entry in tracking_status if entry["group_number"] == group_number), None) # 'next' iterates over 'tracking_status'

    # check if an entry for the current group number already exists in the tracking status
    if group_entry:
        # increment the tracked times by 1
        group_entry["tracked_times"] += 1
        # update the 'last tracked' field of the entry with the current date and time
        group_entry["last_tracked"] = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    else:
        # if no existing entry for the group found the tracking status, create a new entry
        tracking_status.append({
            "group_number": group_number,
            "original_creation_time": original_creation_time,
            "tracked_times": 1,
            "last_tracked": datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        })

    # Convert the updated tracking status list to a JSON string
    new_content = json.dumps(tracking_status, indent=4)
    # Write the updated group tracking status back to Dropbox
    write_file_to_dropbox(dbx, tracking_status_file, new_content)

def get_original_creation_time(dbx,
                               group_number,
                               log_file="/Dissertation/weibo_data/records_and_logs/keyword_output_log.json"):
    """Extracts the original creation time for a given group number from keyword_output_log.json."""
    # Read the log file content from Dropbox
    content = read_file_from_dropbox(dbx, log_file)
    # If the file is not found, return "Unknown"
    if content is None:
        print("keyword_output_log file not found in Dropbox.")
        return "Unknown"

    # opens the log file and loads its JSON content into the variable 'log_data'
    log_data = json.loads(content)
    # Iterate over each log entry to find matching group number
    for entry in log_data:
        if entry["group_number"] == group_number:
            return entry["creation_time"]

    # If no matching entry is found, return "unknown"
    print(f"No entry found for group number: {group_number}")
    return "Unknown"

def log_error(dbx, error_message, error_log_file="/Dissertation/weibo_data/records_and_logs/repost_error_log.json"):
    """
    Log errors to repost_error_log.json in Dropbox
    """
    # Create a dictionary with the error data
    error_data = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        "error": error_message
    }

    # Read existing error data from Dropbox
    content = read_file_from_dropbox(dbx, error_log_file)
    # Load it as JSON, else start with an empty list
    data = json.loads(content) if content else []

    # Append the new error data
    data.append(error_data)
    # Convert the updated error data list to a JSON string
    new_content = json.dumps(data, indent=4)
    # Write the updated error back to Dropbox
    write_file_to_dropbox(dbx, error_log_file, new_content)

if __name__ == "__main__":
    #access_token = ('')
    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        print("Dropbox access token not found.")
        exit(1)

    # Initializes the Dropbox client with the access token
    dbx = dropbox.Dropbox(access_token)

    # Rename the output file
    new_file_name, success = rename_output_file(dbx)

    # Performing the logging process
    log(dbx, new_file_name)