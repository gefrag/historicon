import json
import sys

import requests
from dotenv import dotenv_values

BASE_URL = "https://api.spotify.com/v1"
SHOW_ID = "0tuGt4hA4FRFjiq6lDkojx"
REQUEST_TIMEOUT_SECONDS = 30
secrets = dotenv_values()


class SpotifyApiError(RuntimeError):
    pass


def get_required_secret(name):
    value = secrets.get(name)
    if not value:
        raise SpotifyApiError(f"Missing required secret: {name}")
    return value


def spotify_request(method, url, **kwargs):
    try:
        response = requests.request(
            method,
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            **kwargs,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        message = str(exc)
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                error = response.json().get("error", {})
                spotify_message = error.get("message")
                if spotify_message:
                    message = f"{message}: {spotify_message}"
            except ValueError:
                if response.text:
                    message = f"{message}: {response.text[:200]}"
        raise SpotifyApiError(f"Spotify API request failed: {message}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise SpotifyApiError("Spotify API returned invalid JSON") from exc


def get_access_token():
    client_id = get_required_secret("client_id")
    client_secret = get_required_secret("client_secret")
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = spotify_request("post", token_url, data=data, headers=headers)
    access_token = payload.get("access_token")
    if not access_token:
        raise SpotifyApiError("Spotify token response did not include access_token")
    return access_token


def main():
    all_episodes = {}
    url = f"{BASE_URL}/shows/{SHOW_ID}/episodes"
    headers = {"Authorization": f"Bearer {get_access_token()}"}

    payload = spotify_request("get", url, headers=headers)
    next_url = payload.get("next")
    all_episodes |= payload

    while next_url:
        payload = spotify_request("get", next_url, headers=headers)
        items = payload.get("items")
        if items is None:
            raise SpotifyApiError("Spotify episodes response did not include items")
        all_episodes["items"] += items
        next_url = payload.get("next")

    with open("all_episodes.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(all_episodes, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except SpotifyApiError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
