import requests
import os
import time

# ── Settings ──────────────────────────────────────────
project_id = "r3w56"
token      = "UMIod2Gpqi1ozIuHXogTw9O6h8o4YINb5sqxpGqdVrNp4bCyCuhrIpK6UFwSLChHvvcUwE"
local_folder = r"C:/Users/mvmigem/Documents/data/project_2/low-level-prediction"
# ──────────────────────────────────────────────────────

headers  = {"Authorization": f"Bearer {token}"}
base_url = f"https://files.osf.io/v1/resources/{project_id}/providers/osfstorage/"

def create_folder(osf_folder_path):
    """Create a folder on OSF if it doesn't exist."""
    parts = osf_folder_path.strip("/").split("/")
    current_path = ""
    for part in parts:
        url = f"{base_url}{current_path}?kind=folder&name={part}"
        response = requests.put(url, headers=headers)
        if response.status_code in (200, 201):
            print(f"  📁 Created folder: {current_path}{part}/")
        current_path += part + "/"

def upload_file(local_path, osf_folder_path, retries=3):
    """Upload a file with retry logic and chunked streaming."""
    filename  = os.path.basename(local_path)
    file_size = os.path.getsize(local_path)
    upload_url = f"{base_url}{osf_folder_path}?name={filename}"

    print(f"Uploading {filename} ({file_size / 1024 / 1024:.1f} MB)...")

    for attempt in range(1, retries + 1):
        try:
            with open(local_path, 'rb') as f:
                response = requests.put(
                    upload_url,
                    data=f,
                    headers=headers,
                    timeout=300  # 5 minute timeout for large files
                )
            if response.status_code in (200, 201):
                print(f"  ✓ Uploaded: {filename}")
                return
            else:
                print(f"  ✗ Attempt {attempt} failed: {response.status_code}")
                print(f"    {response.text[:200]}")
        except Exception as e:
            print(f"  ✗ Attempt {attempt} error: {e}")

        if attempt < retries:
            print(f"  ⏳ Retrying in 5 seconds...")
            time.sleep(5)

    print(f"  ✗ Gave up on {filename} after {retries} attempts")

def upload_folder(local_folder):
    for root, dirs, files in os.walk(local_folder):
        relative_path = os.path.relpath(root, local_folder)

        if relative_path == ".":
            osf_path = ""
        else:
            osf_path = relative_path.replace("\\", "/") + "/"
            create_folder(osf_path)  # create folder on OSF first

        for filename in files:
            local_path = os.path.join(root, filename)
            upload_file(local_path, osf_path)
            time.sleep(1)  # small delay between uploads

print("Starting upload...")
upload_folder(local_folder)
print("\nAll done!")