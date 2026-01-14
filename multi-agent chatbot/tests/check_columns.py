import pandas as pd

# Load the CSV
df = pd.read_csv('data/sp500_companies.csv')

print("Actual columns in CSV:")
print("=" * 60)
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")

print("\n" + "=" * 60)
print(f"Total columns: {len(df.columns)}")
print(f"Total rows: {len(df)}")

print("\nFirst row sample:")
print(df.head(1).to_dict('records')[0])