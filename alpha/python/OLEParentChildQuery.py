import pandas as pd

# Load the CSV files into DataFrames
products_df = pd.read_csv('C:\\Users\\BenjaminLee\\Downloads\\Product-2278_20240806095136.csv', encoding='ISO-8859-1')
bundle_timeline_df = pd.read_csv('C:\\Users\\BenjaminLee\\Downloads\\BundleTimeline-2287_20240806095227.csv', encoding='ISO-8859-1')


# Filter the Products DataFrame for records with Type = "OnlineExpert"
online_expert_products = products_df[products_df['Type'] == 'OnlineExpert']

# Filter the BundleTimeline DataFrame for records with Status = "Active"
active_bundles = bundle_timeline_df[bundle_timeline_df['Sample Status'] == 'Active']

# Merge the active bundles with the filtered products to find matching child products
merged_df = active_bundles.merge(
    online_expert_products[['Sample Record ID', 'Description']],
    left_on='ChildProductID',
    right_on='Sample Record ID',
    suffixes=('_bundle', '_child')
)

# Merge again to get parent product descriptions
final_df = merged_df.merge(
    products_df[['Sample Record ID', 'Description']],
    left_on='ParentProductID',
    right_on='Sample Record ID',
    suffixes=('_child', '_parent')
)

# Select the required columns
result_df = final_df[['ParentProductID', 'Description_parent', 'ChildProductID', 'Description_child']]

# Rename columns for clarity
result_df.columns = ['Parent Product ID', 'Parent Product Description', 'Child Product ID', 'Child Product Description']

# Display the result
print(result_df)

# Optionally, save the result to a new CSV file
result_df.to_csv('C:\\Users\\BenjaminLee\\Downloads\\FilteredBundleTimeline.csv', index=False)