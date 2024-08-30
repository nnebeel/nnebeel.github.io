import requests
import base64
import certifi
import time

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

# Function to get total number of pop tracks by year
def get_pop_track_count_by_year(year, access_token):
    search_url = 'https://api.spotify.com/v1/search'
    search_headers = {
        'Authorization': 'Bearer ' + access_token
    }
    search_params = {
        'q': f'genre:pop year:{year}',
        'type': 'track',
        'limit': 1  # We only need one result to get the total count
    }
    search_response = requests.get(search_url, headers=search_headers, params=search_params, verify=certifi.where())
    if search_response.status_code == 429:  # Rate limit exceeded
        retry_after = int(search_response.headers.get('Retry-After', 1))
        print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        return get_pop_track_count_by_year(year, access_token)  # Retry after delay
    search_results = search_response.json()
    return search_results['tracks']['total']

# Example usage
client_id = 'c456b8400783461181b307bf1e60c0d9'
client_secret = '9576388a91f74be49fc8a9b96eb93449'
access_token = get_spotify_token(client_id, client_secret)

years = range(1900, 2025)  # Adjust years as needed

pop_track_counts = []

for year in years:
    print(f"Fetching track count for year: {year}")
    total_tracks = get_pop_track_count_by_year(year, access_token)
    pop_track_counts.append({'year': year, 'total_tracks': total_tracks})

# Print results
for entry in pop_track_counts:
    print(f"{entry['year']} - Total Pop Tracks: {entry['total_tracks']}")

# Optionally, write results to a CSV file
import csv
with open('pop_track_counts.csv', mode='w', newline='', encoding='utf-8') as csv_file:
    fieldnames = ['year', 'total_tracks']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for entry in pop_track_counts:
        writer.writerow(entry)
