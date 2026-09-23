import pandas as pd

print("🔥 AGRICHAIN FINAL AGRICULTURAL FILTER 🔥")

# ==========================================================
# 1. LOAD FULL PRICECATCHER DATA
# ==========================================================

print("\n[1] Loading pricecatcher_full.csv...")

df = pd.read_csv("pricecatcher_full.csv")

print(f"Original records: {len(df)}")


# ==========================================================
# 2. CLEAN TEXT COLUMNS
# ==========================================================

df["item_group"] = df["item_group"].fillna("").str.strip().str.upper()
df["item_category"] = df["item_category"].fillna("").str.strip().str.upper()
df["item"] = df["item"].fillna("").str.strip()


# ==========================================================
# 3. SELECT AGRICULTURAL CATEGORIES
# ==========================================================

agricultural_categories = [
    "SAYUR-SAYURAN",
    "BUAH-BUAHAN",
    "UBI KENTANG"
]


# ==========================================================
# 4. FILTER AGRICULTURAL PRODUCTS
# ==========================================================

print("\n[2] Filtering agricultural products...")

df_agri = df[
    (
        df["item_group"] == "BARANGAN SEGAR"
    )
    &
    (
        df["item_category"].isin(agricultural_categories)
    )
].copy()


# ==========================================================
# 5. REMOVE EMPTY / INVALID DATA
# ==========================================================

df_agri = df_agri[
    (df_agri["item"].notna())
    &
    (df_agri["item"] != "")
    &
    (df_agri["price"].notna())
    &
    (df_agri["price"] > 0)
].copy()


# ==========================================================
# 6. SELECT COLUMNS NEEDED FOR AGRICHAIN
# ==========================================================

df_agri = df_agri[
    [
        "date",
        "item_code",
        "item",
        "unit",
        "item_group",
        "item_category",
        "price",
        "premise_code",
        "premise",
        "premise_type",
        "state",
        "district"
    ]
]


# ==========================================================
# 7. SORT DATA
# ==========================================================

df_agri = df_agri.sort_values(
    by=["date", "item"],
    ascending=[True, True]
).reset_index(drop=True)


# ==========================================================
# 8. DISPLAY RESULTS
# ==========================================================

print("\n[3] FILTER COMPLETE!")

print(f"Final agricultural records: {len(df_agri)}")

print("\nAgricultural commodities available:")

items = (
    df_agri[
        [
            "item_code",
            "item",
            "unit",
            "item_category"
        ]
    ]
    .drop_duplicates()
    .sort_values("item")
)

print(items.to_string(index=False))


# ==========================================================
# 9. DISPLAY STATES
# ==========================================================

print("\n[4] States available:")

states = (
    df_agri["state"]
    .dropna()
    .drop_duplicates()
    .sort_values()
)

for state in states:
    print("-", state)


# ==========================================================
# 10. SAVE FINAL DATASET
# ==========================================================

df_agri.to_csv(
    "agrichain_prices.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n✅ FINAL DATASET SAVED!")
print("📁 File: agrichain_prices.csv")
print(f"📊 Total records: {len(df_agri)}")
print("🇲🇾 All Malaysian states retained.")
print("🌱 Agricultural products only.")