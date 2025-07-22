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

def create_paste(paste_text):
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
        sys.exit(1)
    input_file = sys.argv[1]
    if input_file == '!':
        print(get_most_recent_paste())
    else:
        with open(input_file, 'r') as file:
            paste_text = file.read()
        create_paste(paste_text)
        print("Paste created")