import json
import os
import base64
import requests
from pathlib import Path


DROPBOX_APP_KEY = "2uswcj7kbg3sb8x"
DROPBOX_APP_SECRET = "e7eu41fdk2vm67v"
DROPBOX_REFRESH_TOKEN = (
    "pO79DuN9AWEAAAAAAAAAAayfLkmNeQBUfwqCHBd1-c0OD9ZBGDQl70a1imnB7Pp4"
)

ACCESS_TOKEN = None


def get_access_token():
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    response = requests.post(
        "https://api.dropbox.com/oauth2/token",
        data={"grant_type": "refresh_token", "refresh_token": DROPBOX_REFRESH_TOKEN},
        auth=(DROPBOX_APP_KEY, DROPBOX_APP_SECRET),
    )
    response.raise_for_status()
    ACCESS_TOKEN = response.json()["access_token"]
    return ACCESS_TOKEN


def download_file(path):
    token = get_access_token()
    response = requests.post(
        "https://content.dropboxapi.com/2/files/download",
        headers={
            "Authorization": f"Bearer {token}",
            "Dropbox-API-Arg": json.dumps({"path": path}),
            "Content-Type": "application/octet-stream",
        },
    )
    response.raise_for_status()
    return response.content


def github_api(method, endpoint, pat, data=None, json_response=True):
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com{endpoint}"

    if method == "GET":
        r = requests.get(url, headers=headers)
    elif method == "POST":
        r = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        r = requests.put(url, headers=headers, json=data)
    elif method == "PATCH":
        r = requests.patch(url, headers=headers, json=data)
    elif method == "DELETE":
        r = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unknown method: {method}")

    if r.status_code >= 400:
        print(f"[!] GitHub API error: {r.status_code} - {r.text}")
        r.raise_for_status()

    return r.json() if json_response else r


def get_repo_public_key(owner, repo, pat):
    data = github_api("GET", f"/repos/{owner}/{repo}/actions/secrets/public-key", pat)
    return data["key_id"], data["key"]


def create_or_update_secret(owner, repo, pat, secret_name, secret_value):
    key_id, key = get_repo_public_key(owner, repo, pat)

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    import binascii

    key_bytes = base64.b64decode(key)

    from nacl import encoding, public

    box = public.PublicKey(key_bytes[:32], encoding.RawEncoder())
    encryptor = public.SealedBox(box)
    encrypted = encryptor.encrypt(secret_value.encode())

    encrypted_b64 = base64.b64encode(encrypted).decode()

    github_api(
        "PUT",
        f"/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        pat,
        data={"encrypted_value": encrypted_b64, "key_id": key_id},
    )


def create_repo(pat, name, description="Z.AI Link Farm Automation"):
    try:
        data = github_api(
            "POST",
            "/user/repos",
            pat,
            data={
                "name": name,
                "description": description,
                "private": False,
                "has_wiki": False,
            },
        )
        print(f"[*] Created repo: {name}")
        return data
    except Exception as e:
        print(f"[!] Repo creation failed (may already exist): {e}")
        return None


def setup_repo(account_num, pat, owner):
    repo_name = f"web-metrics-sync-{account_num}"
    print(f"\n[*] Setting up repo {repo_name} for {owner}...")

    data = github_api("GET", f"/user", pat)
    actual_owner = data["login"]
    print(f"[*] Actual owner: {actual_owner}")

    create_repo(pat, repo_name)

    secrets = {
        "DROPBOX_APP_KEY": DROPBOX_APP_KEY,
        "DROPBOX_APP_SECRET": DROPBOX_APP_SECRET,
        "DROPBOX_REFRESH_TOKEN": DROPBOX_REFRESH_TOKEN,
    }

    print("[*] Adding Dropbox secrets...")
    for name, value in secrets.items():
        try:
            create_or_update_secret(actual_owner, repo_name, pat, name, value)
            print(f"    - {name}: OK")
        except Exception as e:
            print(f"    - {name}: FAILED - {e}")

    return actual_owner, repo_name


if __name__ == "__main__":
    tokens = json.loads(download_file("/dropbox/github-tokens.json").decode())

    for token in tokens[:3]:
        owner, repo = setup_repo(token["id"], token["pat"], f"account-{token['id']}")
        print(f"[*] {repo} ready at https://github.com/{owner}/{repo}")
