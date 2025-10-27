import os
import requests

# GitHub API endpoint for directory contents
API_URL = "https://api.github.com/repos/Macaulay2/M2/contents/M2/Macaulay2/packages/Macaulay2Doc?ref=stable"

# Local save directory
SAVE_DIR = os.path.join('data', 'macaulay2docs')
os.makedirs(SAVE_DIR, exist_ok=True)

# Fetch directory listing
response = requests.get(API_URL)
files = response.json()

def download_dir(api_url, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    response = requests.get(api_url)
    response.raise_for_status()
    for f in response.json():
        if f["type"] == "dir":
            download_dir(f["url"], os.path.join(save_dir, f["name"]))
        elif f["type"] == "file" and f["name"].endswith(".m2"):
            print(f"Downloading {f['path']}...")
            data = requests.get(f["download_url"]).text
            with open(os.path.join(save_dir, f["name"]), "w", encoding="utf-8") as fp:
                fp.write(data)

download_dir(API_URL, SAVE_DIR)
