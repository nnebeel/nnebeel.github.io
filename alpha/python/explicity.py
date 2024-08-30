import requests
import base64
import certifi
import csv
import json

# Function to get Spotify access token
def get_spotify_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_headers = {
        'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode()).decode()
    }
    auth_data = {
        'grant_type': 'client_credentials'
    }
    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data, verify=certifi.where())
    return auth_response.json()['access_token']

# Function to fetch track features
def get_track_features(track_id, access_token):
    features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
    features_headers = {
        'Authorization': 'Bearer ' + access_token
    }
    features_response = requests.get(features_url, headers=features_headers, verify=certifi.where())
    return features_response.json()

# Function to search for track and get its details
def search_track(track_name, artist_name, access_token):
    search_url = 'https://api.spotify.com/v1/search'
    search_headers = {
        'Authorization': 'Bearer ' + access_token
    }
    search_params = {
        'q': f'track:{track_name} artist:{artist_name}',
        'type': 'track',
        'limit': 1
    }
    search_response = requests.get(search_url, headers=search_headers, params=search_params, verify=certifi.where())
    track_info = search_response.json()
    if track_info['tracks']['items']:
        return track_info['tracks']['items'][0]
    else:
        return None

# Load track list from JSON file
with open('alpha\python\explicittracks.json', 'r', encoding='utf-8') as file:
    tracks = json.load(file)

client_id = 'c456b8400783461181b307bf1e60c0d9'
client_secret = '9576388a91f74be49fc8a9b96eb93449'
access_token = get_spotify_token(client_id, client_secret)

# Open CSV file for writing
with open('track_features.csv', mode='w', newline='', encoding='utf-8') as csv_file:
    fieldnames = [
        'year', 'title', 'artist', 'explicit', 'danceability', 'energy', 'key', 'loudness', 
        'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo'
    ]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    for track in tracks:
        track_info = search_track(track['title'], track['artist'], access_token)
        if track_info:
            track_id = track_info['id']
            explicit = track_info['explicit']
            artist_name = track_info['artists'][0]['name']
            features = get_track_features(track_id, access_token)
            
            # Print each title as we parse through the list
            print(f"Parsing: {track['title']} by {artist_name}")
            
            # Collect data for CSV
            row = {
                'year': track['year'],
                'title': track_info['name'],
                'artist': artist_name,
                'explicit': explicit,
                'danceability': features['danceability'],
                'energy': features['energy'],
                'key': features['key'],
                'loudness': features['loudness'],
                'mode': features['mode'],
                'speechiness': features['speechiness'],
                'acousticness': features['acousticness'],
                'instrumentalness': features['instrumentalness'],
                'liveness': features['liveness'],
                'valence': features['valence'],
                'tempo': features['tempo']
            }
            
            writer.writerow(row)
        else:
            print(f"Track: {track['title']} by {track['artist']} not found.")

print("Processing complete. Data saved to 'track_features.csv'.")
