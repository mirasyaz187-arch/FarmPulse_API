import pandas as pd

print("🔥 PRICECATCHER FULL DATA TEST 🔥")

URL_PRICE = "https://storage.data.gov.my/pricecatcher/pricecatcher_2026-09.csv"
URL_ITEM = "https://storage.data.gov.my/pricecatcher/lookup_item.csv"
URL_PREMISE = "https://storage.data.gov.my/pricecatcher/lookup_premise.csv"

try:

    print("\n[1] Downloading price data...")
    df_price = pd.read_csv(URL_PRICE)

    print(f"Price records: {len(df_price)}")
    print("Price columns:")
    print(df_price.columns.tolist())

    print("\n[2] Downloading item lookup...")
    df_item = pd.read_csv(URL_ITEM)

    print(f"Item records: {len(df_item)}")
    print("Item columns:")
    print(df_item.columns.tolist())

    print("\nFirst 5 items:")
    print(df_item.head())

    print("\n[3] Downloading premise lookup...")
    df_premise = pd.read_csv(URL_PREMISE)

    print(f"Premise records: {len(df_premise)}")
    print("Premise columns:")
    print(df_premise.columns.tolist())

    print("\nFirst 5 premises:")
    print(df_premise.head())

except Exception as e:

    print("\n❌ ERROR:")
    print(e)