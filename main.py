import json

import requests
from dotenv import dotenv_values

BASE_URL = "https://api.spotify.com/v1"
SHOW_ID = "0tuGt4hA4FRFjiq6lDkojx"
secrets = dotenv_values()
client_id = secrets["client_id"]
client_secret = secrets["client_secret"]


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


def get_access_token():
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=data, headers=headers)
    return response.json()["access_token"]


def main():
    all_episodes = {}
    url = f"{BASE_URL}/shows/{SHOW_ID}/episodes"
    headers = {"Authorization": f"Bearer {get_access_token()}"}

    a = requests.get(url, headers=headers)
    next_url = a.json()["next"]
    all_episodes |= a.json()

    while next_url:
        a = requests.get(next_url, auth=BearerAuth(get_access_token()))
        all_episodes["items"] += a.json()["items"]
        next_url = a.json().get("next")

    with open("all_episodes.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(all_episodes, ensure_ascii=False))


if __name__ == "__main__":
    main()
