import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# Load the data with proper quoting
data = pd.read_csv('video_tags.csv', quotechar='"', quoting=1, on_bad_lines='skip')

# Ensure all tags are strings and replace NaN with empty strings
data['tags'] = data['tags'].fillna('').astype(str)

# Split tags into individual tags and then combine them for each channel
data['tags'] = data['tags'].apply(lambda x: ' '.join(x.split(',')))

# Combine tags for each channel
channel_tags = data.groupby('channel')['tags'].apply(lambda x: ' '.join(x)).reset_index()

# Vectorize the tags using TF-IDF with additional preprocessing
vectorizer = TfidfVectorizer(stop_words='english', max_df=0.5, min_df=2)
X = vectorizer.fit_transform(channel_tags['tags'])

# Increase the number of clusters
num_clusters = 20  # Adjusted number of clusters
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
channel_tags['cluster'] = kmeans.fit_predict(X)

# Save the clustering results
channel_tags.to_csv('channel_clusters.csv', index=False, encoding='utf-8')

# Print the clusters and channels with proper encoding handling
import sys
import io

# Redirect standard output to handle Unicode characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

for cluster in range(num_clusters):
    print(f'Cluster {cluster}:')
    cluster_channels = channel_tags[channel_tags['cluster'] == cluster]['channel'].tolist()
    print(', '.join(cluster_channels))
    print()

print('Clustering completed and saved to channel_clusters.csv')
