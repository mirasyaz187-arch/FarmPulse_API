import pandas as pd

URL_PRICE = "https://storage.data.gov.my/pricecatcher/pricecatcher_2026-09.csv"
URL_ITEM = "https://storage.data.gov.my/pricecatcher/lookup_item.csv"
URL_PREMISE = "https://storage.data.gov.my/pricecatcher/lookup_premise.csv"


def get_pricecatcher_data():

    print("🔥 PRICECATCHER LOADER 🔥")

    # 1. Download price data
    print("[1] Downloading price data...")
    df_price = pd.read_csv(URL_PRICE)

    # 2. Download item information
    print("[2] Downloading item information...")
    df_item = pd.read_csv(URL_ITEM)

    # 3. Download premise information
    print("[3] Downloading premise information...")
    df_premise = pd.read_csv(URL_PREMISE)

    # 4. Merge price + item
    print("[4] Combining price + item...")

    df = df_price.merge(
        df_item,
        on="item_code",
        how="left"
    )

    # 5. Merge + premise
    print("[5] Combining + premise...")

    df = df.merge(
        df_premise,
        on="premise_code",
        how="left"
    )

    print("\n✅ DATA SUCCESSFULLY COMBINED!")
    print(f"Total records: {len(df)}")

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 10 records:")
    print(df.head(10))

    return df


if __name__ == "__main__":

    df = get_pricecatcher_data()

    df.to_csv(
        "pricecatcher_full.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\n✅ Saved as pricecatcher_full.csv")