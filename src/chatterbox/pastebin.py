import requests
import xml.etree.ElementTree as ET
import base64

def encode(text, password):
    enc = []
    for i in range(len(text)):
        key_c = password[i % len(password)]
        enc_c = chr((ord(text[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    encoded_bytes = "".join(enc).encode()
    return base64.urlsafe_b64encode(encoded_bytes).decode()

def decode(encoded_text, password):
    enc = base64.urlsafe_b64decode(encoded_text).decode()
    dec = []
    for i in range(len(enc)):
        key_c = password[i % len(password)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)



api_dev_key = 'HNKedNEoBzYurdcai02udNLBx_rymUys'
api_user_name = 'arozventi'     
api_user_password = ',";7S9S:CSSRpHe' # Throwaway account so doesn't matter

def get_user_key():
    # Step 1: Get the user key
    login_data = {
        'api_dev_key': api_dev_key,
        'api_user_name': api_user_name,
        'api_user_password': api_user_password
    }
    login_response = requests.post("https://pastebin.com/api/api_login.php", data=login_data)
    api_user_key = login_response.text.strip()
    return api_user_key

def delete_paste(paste_key):
    """Delete a specific paste by its key."""
    data = {
        'api_option': 'delete',
        'api_dev_key': api_dev_key,
        'api_user_key': get_user_key(),
        'api_paste_key': paste_key
    }
    response = requests.post("https://pastebin.com/api/api_post.php", data=data)
    return response.text.strip()

def delete_all_pastes():
    """Delete all existing pastes for the user."""
    # Step 1: Get list of all pastes
    data = {
        'api_option': 'list',
        'api_dev_key': api_dev_key,
        'api_user_key': get_user_key(),
        'api_results_limit': 1000  # Get maximum number
    }

    response = requests.post("https://pastebin.com/api/api_post.php", data=data)
    response.raise_for_status()

    # Step 2: Parse the XML response
    if response.text.strip() == "No pastes found.":
        print("No pastes to delete.")
        return

    fixed_xml = f"<root>{response.text}</root>"
    root = ET.fromstring(fixed_xml)

    pastes = root.findall('paste')
    if not pastes:
        print("No pastes found.")
        return

    # Step 3: Delete each paste
    deleted_count = 0
    for paste in pastes:
        paste_key = paste.find('paste_key').text
        paste_title = paste.find('paste_title').text
        result = delete_paste(paste_key)
        if "Paste Removed" in result:
            print(f"Deleted: {paste_title} ({paste_key})")
            deleted_count += 1
        else:
            print(f"Failed to delete: {paste_title} ({paste_key}) - {result}")
    
    print(f"Successfully deleted {deleted_count} paste(s).")

def create_paste(paste_text, delete_existing=False):
    """Create a new paste, optionally deleting existing pastes first."""
    if delete_existing:
        print("Deleting existing pastes...")
        delete_all_pastes()
    
    # Step 2: Create a new paste
    data = {
        'api_option': 'paste',
        'api_dev_key': api_dev_key,
        'api_user_key': get_user_key(),
        'api_paste_code': encode(paste_text, 'gellybean'),
        'api_paste_name': 'Narration Upload',  # Optional: set a title
        'api_paste_private': '1',              # 0=public, 1=unlisted, 2=private
        'api_paste_expire_date': 'N',          # 'N' for never expire
    }
    response = requests.post("https://pastebin.com/api/api_post.php", data=data)
    print("Paste URL:", response.text)

def get_most_recent_paste():
    # Step 1: Fetch a list of pastes
    data = {
        'api_option': 'list',
        'api_dev_key': api_dev_key,
        'api_user_key': get_user_key(),
        'api_results_limit': 50
    }

    response = requests.post("https://pastebin.com/api/api_post.php", data=data)
    response.raise_for_status()

    # Step 2: Wrap the result in a root tag so it becomes valid XML
    fixed_xml = f"<root>{response.text}</root>"
    root = ET.fromstring(fixed_xml)

    pastes = root.findall('paste')
    if not pastes:
        print("No pastes found.")
        return None

    # Step 3: Find the paste with the most recent date
    most_recent = max(pastes, key=lambda p: int(p.find('paste_date').text))
    paste_key = most_recent.find('paste_key').text
    paste_title = most_recent.find('paste_title').text

    # Step 4: Fetch the raw content of that paste
    raw_url = f"https://pastebin.com/raw/{paste_key}"
    raw_response = requests.get(raw_url)
    raw_response.raise_for_status()

    content = raw_response.text
    return decode(content, 'gellybean')


import sys 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pastebin.py <input_file>")
        print("       python pastebin.py ! (to get most recent paste)")
        print("       python pastebin.py --delete-all (to delete all pastes)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if input_file == '!':
        print(get_most_recent_paste())
    elif input_file == '--delete-all':
        delete_all_pastes()
    else:
        # Check if user wants to delete existing pastes first
        delete_existing = True# '--delete-existing' in sys.argv
        
        with open(input_file, 'r') as file:
            paste_text = file.read()
        create_paste(paste_text, delete_existing=delete_existing)
        print("Paste created")