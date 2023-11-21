# Updated at 2023-11-20; Interacts with Dropbox for the group number and logging operations.

# This file does the following things:
# (1) creates/increments group number every time it runs
# (2) rename the output file into "creation time_group number"
# (3) maintains a "keyword_output_log" file that records the file name, creation time, group number, and success
# (4) maintain a "keyword_error_log" file that records the failed cases of keyword tracking

import datetime
import os # used to check the existence of files
import json
import dropbox



def read_file_form_dropbox(dbx, file_path):
    """
    Reads a file's contents from Dropbox.
    :param dbx: Dropbox's client instance
    :param file_path: path of the file in Dropbox
    :return: Returns the file's contents as a string, or None if an error occurs
    """
    try:
        _, res = dbx.files_download(file_path)
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

def get_group_number(dbx, filename="/Dissertation/weibo_data/records_and_logs/group_number.txt"):
    """The function returns the new group number"""
    content = read_file_form_dropbox(dbx, filename)
    if content:
        last_group_number = int(content.strip())
    else:
        last_group_number = 0


    # Increment the group number
    group_number = last_group_number + 1

    # Write the new group number back to the file
    write_file_to_dropbox(dbx, filename, str(group_number))

    return group_number

def update_log(dbx, log_data, output_log_file):
    """The function updates the output log"""
    # check if the log file exists; if not, creates the file and write the log data
    content = read_file_form_dropbox(dbx, output_log_file)
    if content:
        data = json.loads(content)
    else:
        data = []

    data.append(log_data)
    new_content = json.dumps(data, indent=4)
    write_file_to_dropbox(dbx, output_log_file, new_content)

def log_error(dbx, error_message, error_log_file):
    """The function to log errors"""
    # prepare the error data
    content = read_file_form_dropbox(dbx, error_log_file)
    if content:
        data = json.loads(content)
    else:
        data = []

    error_data = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        "error": error_message
    }
    data.append(error_data)
    new_content = json.dumps(data, indent=4)
    write_file_to_dropbox(dbx, error_log_file, new_content)

def rename_output_file(dbx,
                       group_number,
                       local_output_dir,
                       dropbox_output_dir,
                       output_log_file,
                       error_log_file):
    """The function renames the output file and upload the log file"""
    # get the current date and time, formatting it in a readable string format
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d-%H-%M-%S")

    # create the file name using the formatted time and group number
    data_file_name = f"{formatted_time}_group_{group_number}.jsonl"

    # Path for the renamed file in the local environment
    local_new_file_path = os.path.join(local_output_dir, data_file_name)

    # Path for the file in Dropbox
    dropbox_file_path = os.path.join(dropbox_output_dir, data_file_name)

    # flag to check if a file has been found and renamed
    found_file = False

    # rename the output file to the generated data file name
    for filename in os.listdir(local_output_dir):
        if filename.endswith('.jsonl'): # replace with file extension
            new_filename = data_file_name # the new file name
            original_file_path = os.path.join(local_output_dir, filename) # construct the full path to the original file
            os.rename(original_file_path, local_new_file_path) # rename the file, moving it from the original path to the new path with the new file name
            print(f"Data file {filename} has been renamed to : {new_filename}")
            upload_file_to_dropbox(dbx, local_new_file_path, dropbox_file_path)
            print(f"Data file {new_filename} has been uploaded to Dropbox.")
            found_file = True # update the flag to indicate a file has been renamed
            break # NOTE: Here assuming only one file needs to be renamed

    # prepare the log data, with success marked as True
    log_data = {
        "file_name": data_file_name if found_file else "None",
        "creation_time": formatted_time,
        "group_number": group_number,
        "success": found_file
    }

    # write log data to the output log file
    update_log(dbx, log_data, output_log_file)

    # if no file was found and renamed, log the error to the error log file
    if not found_file:
        error_message = f"No output file found for group {group_number}"
        log_error(dbx, error_message, error_log_file)
        print(error_message)
        return None, False

    # return the new file name if a file was found and renamed
    return data_file_name if found_file else None

if __name__ == "__main__":
    access_token = ('sl.BqTpRn_xJK-wo6YWped4itwEzmfwFLgd8HW3hp-kxj7mb44NKCkuKjM9lojKLgtM6iNYEp7RSwbEo096wdT1zA_OQrK94KTc5m2ZdV4aSsFEUhN-9KzFB7CTd0DhalaBsMf0QYqTJeeH')
    if not access_token:
        print("Dropbox access token not found.")
        exit(1)

    dbx = dropbox.Dropbox(access_token)

    # Get the new group number from Dropbox
    group_number = get_group_number(dbx)

    # Rename the output file locally (assuming this part is unchanged)
    rename_output_file(dbx,
                       group_number,
                       "../output/",
                       "/Dissertation/weibo_data/keyword_output/",
                       "/Dissertation/weibo_data/records_and_logs/keyword_output_log.json",
                       "/Dissertation/weibo_data/records_and_logs/keyword_error_log.json")






