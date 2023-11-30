# Updated at 2023-11-20; Interacts with Dropbox for recoding and logging operations.

# This script
# (1) determine which groups to track
# (2) store the list of groups to a txt file
# (3) generate a list of post IDs for feedback tracking
# (4) store the list of post IDs to a txt file

import json
import os
import datetime
import dropbox # added to import the Dropbox SDK

def read_file_from_dropbox(dbx, file_path):
    """
    Reads a file's contents from Dropbox.
    :param dbx: Dropbox's client instance
    :param file_path: path of the file in Dropbox
    :return: Returns the file's contents as a string, or None if an error occurs
    """
    # Tries to download the file from Dropbox
    try:
        _, res = dbx.files_download(file_path)
        # Returns file contents as a string
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
    # Tries to upload content to a specified file in Dropbox
    try:
        dbx.files_upload(content.encode('utf-8'), file_path, mode=dropbox.files.WriteMode("overwrite"))
    except dropbox.exceptions.ApiError as e:
        print(f"Error writing file to Dropbox: {file_path}")


def get_groups_to_track(dbx,
                        log_file_path="/Dissertation/weibo_data/records_and_logs/keyword_output_log.json",
                        tracking_window_hours=48):
    """
    Determines which groups to track based on the creation time in keyword_output_file_log.json
    :param dbx: Dropbox client instance.
    :param log_file_path: Path of the keyword output log.
    :param tracking_window_hours: the time window for tracking
    :return (1) a list of groups (2) a txt file that stores this list - groups_to_track.txt (3) a txt fle that stores
    only the group number of that list - group_number_range.txt"""

    # Reads the log file from Dropbox and checks if the log file was successfully read
    log_file = read_file_from_dropbox(dbx, log_file_path)
    if log_file is None:
        print("Log file does not exist.")
        return [], [] # returns two empty lists if the file is not found (groups to track and group range)

    # Loads the file content
    log_data = json.loads(log_file)

    # Get the current time and initialize an empty list 'groups to track' for storing the names of files that
    # are within the tracking window
    current_time = datetime.datetime.now()
    groups_to_track = []
    group_range = []

    # Iterates over each entry in the log data
    for entry in log_data:
        # converts 'creation time' from a string to a 'datetime' object
        creation_time = datetime.datetime.strptime(entry["creation_time"], "%Y-%m-%d-%H-%M-%S")
        # calculate the 'age' of each file
        age_hours = (current_time - creation_time).total_seconds() / 3600

        # if the age of the file is between 0-48 hours, add it to the list
        if 0 <= age_hours <= tracking_window_hours:
            groups_to_track.append(entry["file_name"])
            group_range.append(entry["group_number"])

    # compiles lists of files and group numbers into text content
    groups_content = "\n".join(groups_to_track)
    group_range_content = "\n".join(map(str, group_range))

    # Writes the compiled lists to Dropbox files
    write_file_to_dropbox(dbx, "/Dissertation/weibo_data/records_and_logs/groups_to_track.txt", groups_content)
    write_file_to_dropbox(dbx, "/Dissertation/weibo_data/records_and_logs/group_number_range.txt", group_range_content)

    return groups_to_track, group_range


# Generate the list of post IDs that need to be tracked
def combine_posts_from_groups(dbx, files_to_track, base_directory="/Dissertation/weibo_data/keyword_output"):
    """
    Combines all posts in the groups identified and returns a list of post IDs
    :param dbx: Dropbox client instance.
    :param files_to_track: files that need to be tracked as returned by the get_groups_to_track function
    :param base_directory: path that stores all keyword output files
    """
    unique_ids = set() # using a set to avoid duplicates

    # Iterates over each file in the list of files to track
    for file_name in files_to_track:
        file_path = os.path.join(base_directory, file_name) # construct the full file path
        file_content = read_file_from_dropbox(dbx, file_path) # read the file from Dropbox

        # Check if file content was successfully retrieved
        if file_content is None:
            print(f"Could not read from Dropbox: {file_path}")
            continue

        # Processes each line in the file content
        for line in file_content.splitlines():
            try:
                # Parse each line as a JSON object
                entry = json.loads(line)
                # extract the 'mblogid' and add to the set
                unique_ids.add(entry['mblogid'])
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {file_name}")

    return list(unique_ids)

def save_post_ids_to_file(dbx,
                          combined_post_ids,
                          filename="/Dissertation/weibo_data/records_and_logs/combined_post_ids.txt"):
    """Saves the list of post IDs to a text file"""
    # Joins the list of post IDs into a single string with each ID on a new line
    content = '\n'.join(combined_post_ids)
    # Writes the content to a Dropbox file
    write_file_to_dropbox(dbx, filename, content)
    print(f"Post IDs saved to {filename}")


if __name__ == "__main__":
    # Retrieve the Dropbox access token
    #access_token = ('')
    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        print("Dropbox access token not found.")
        exit(1)

    # Initializes the Dropbox client with the access token
    dbx = dropbox.Dropbox(access_token)

    # Get the list of file names to track
    files_to_track, group_range = get_groups_to_track(dbx)
    print("Files to track:", files_to_track)
    print("Group numbers to track", group_range)

    # Get the combined list of post IDs
    combined_post_ids = combine_posts_from_groups(dbx, files_to_track)
    print("Posts to be tracked:", combined_post_ids)

    # save post ids to dropbox
    save_post_ids_to_file(dbx, combined_post_ids, "/Dissertation/weibo_data/records_and_logs/combined_post_ids.txt")

