import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from tkinter import Tk, simpledialog
import seaborn as sns  # For better color handling

# Load the CSV file
file_path = "C:\\Users\\BenjaminLee\\LearnKey, Inc\\Development - Documents\\LMS\\Course categories for k-means.csv"
data = pd.read_csv(file_path)

# Convert 1s and blanks to binary (1 and 0)
binary_data = data.iloc[:, 1:].fillna(0).astype(int)

# Standardize the data
scaler = StandardScaler()
scaled_data = scaler.fit_transform(binary_data)

# PCA for dimensionality reduction
pca = PCA(n_components=2)
pca_data = pca.fit_transform(scaled_data)

# Determine the optimal number of clusters using the elbow method
sse = []
k_range = range(1, 25)  # Testing k from 1 to 10

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(scaled_data)
    sse.append(kmeans.inertia_)

    # Automatically detect the elbow point
def detect_elbow(sse, k_range):
    sse_diff = np.diff(sse)
    sse_diff_ratio = sse_diff[1:] / sse_diff[:-1]
    elbow = np.argmin(sse_diff_ratio) + 2  # +2 because of the diff and index offset
    return elbow

optimal_k = detect_elbow(sse, k_range)

# Plot the elbow graph
plt.figure(figsize=(8, 4))
plt.plot(k_range, sse, marker='o')
plt.axvline(x=optimal_k, color='r', linestyle='--', label=f'Optimal k = {optimal_k}')
plt.xlabel('Number of Clusters')
plt.ylabel('Sum of Squared Errors (SSE)')
plt.title('Elbow Method for Optimal k')
plt.xticks(k_range)
plt.grid(True)
plt.legend()
plt.show()

# Use Tkinter for GUI input
root = Tk()
root.withdraw()  # Hide the root window
optimal_k = simpledialog.askinteger("Input", "Enter the optimal number of clusters based on the elbow plot:", initialvalue=optimal_k)

# Perform k-means clustering with optimal_k
kmeans = KMeans(n_clusters=optimal_k, random_state=42)
clusters = kmeans.fit_predict(pca_data)
data['Cluster'] = clusters

# Set color palette
colors = sns.color_palette("hsv", optimal_k)

# Visualize the clusters with labels
plt.figure(figsize=(12, 8))
scatter_plots = []  # To keep track of scatter plots for legend handling

# Loop through each cluster index to maintain color consistency
for cluster_index in range(optimal_k):
    # Filter data points that belong to the current cluster
    cluster_points = pca_data[clusters == cluster_index]
    cluster_labels = data.iloc[clusters == cluster_index, 0]
    
    # Plot each cluster with consistent color and a single legend entry
    scatter_plot = plt.scatter(cluster_points[:, 0], cluster_points[:, 1], color=colors[cluster_index], label=f'Cluster {cluster_index}')
    scatter_plots.append(scatter_plot)
    
    # Optionally, you can add labels to each point
    for point, label in zip(cluster_points, cluster_labels):
        plt.text(point[0], point[1], label, fontsize=9, ha='right')

plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.title('K-Means Clusters with Labels')

# Create a legend using the scatter plots
plt.legend(handles=scatter_plots, bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True)
plt.show()

# Extract relevant data for export
export_data = data[['Cluster', data.columns[0]]]  # Assuming the first column contains the item names
export_data.columns = ['Cluster', 'Item']  # Renaming columns for clarity

# Sort data by cluster for easier readability
export_data = export_data.sort_values(by=['Cluster', 'Item'])

# Export cluster contents to a single CSV
output_file_path = "C:\\Users\\BenjaminLee\\LearnKey, Inc\\Development - Documents\\LMS\\Course clusters output.csv"  # Specify your output file name and path
export_data.to_csv(output_file_path, index=False)

