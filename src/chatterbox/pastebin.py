import requests
import xml.etree.ElementTree as ET

api_dev_key = 'HNKedNEoBzYurdcai02udNLBx_rymUys'

api_user_name = 'arozventi'     
api_user_password = ',";7S9S:CSSRpHe' # Throwaway account so doesn't matter

# Step 1: Get the user key
login_data = {
    'api_dev_key': api_dev_key,
    'api_user_name': api_user_name,
    'api_user_password': api_user_password
}
login_response = requests.post("https://pastebin.com/api/api_login.php", data=login_data)
api_user_key = login_response.text.strip()


def create_paste(paste_text):
    # Step 2: Create a new paste
    data = {
        'api_option': 'paste',
        'api_dev_key': api_dev_key,
        'api_user_key': api_user_key,
        'api_paste_code': paste_text,
        'api_paste_name': 'Narration Upload',  # Optional: set a title
        'api_paste_private': '1',              # 0=public, 1=unlisted, 2=private
        'api_paste_expire_date': 'N',          # 'N' for never expire
    }
    response = requests.post("https://pastebin.com/api/api_post.php", data=data)
    print("Paste URL:", response.text)


def get_most_recent_paste():
    # Step 1: Get metadata for the most recent paste
    list_data = {
        'api_option': 'list',
        'api_dev_key': api_dev_key,
        'api_user_key': api_user_key,
        'api_results_limit': 1
    }

    list_response = requests.post("https://pastebin.com/api/api_post.php", data=list_data)
    list_response.raise_for_status()
    
    # Step 2: Parse XML response to get the paste key
    root = ET.fromstring(list_response.text)
    paste_key = root.find('paste_key').text

    # Step 3: Fetch the raw text of that paste
    raw_url = f"https://pastebin.com/raw/{paste_key}"
    raw_response = requests.get(raw_url)
    raw_response.raise_for_status()
    paste_text = raw_response.text


    return paste_text

import sys 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pastebin.py <input_file>")
        sys.exit(1)
    input_file = sys.argv[1]
    with open(input_file, 'r') as file:
        paste_text = file.read()
    create_paste(paste_text)
    print("Paste created")