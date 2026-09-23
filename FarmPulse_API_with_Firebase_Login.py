from fastapi import FastAPI, Query
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import hashlib
import hmac
import os

# Firebase / Firestore
from firebase_config import db


# ==========================================
# PASSWORD SECURITY
# ==========================================

def hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )

    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)

        salt = bytes.fromhex(salt_hex)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000
        )

        return hmac.compare_digest(
            password_hash.hex(),
            hash_hex
        )

    except Exception:
        return False


# ==========================================
# LOGIN / REGISTER MODELS
# ==========================================

class RegisterRequest(BaseModel):
    name: str
    phone: str
    password: str
    role: str = "farmer"


class LoginRequest(BaseModel):
    phone: str
    password: str


# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(
    title="FarmPulse API",
    description="Agricultural Price Monitoring API",
    version="1.0"
)


# ==========================================
# STARTING MESSAGE
# ==========================================

print("==========================================")
print("🔥 AGRICHAIN API STARTING...")
print("==========================================")


# ==========================================
# LOAD DATASET
# ==========================================

try:

    df_prices = pd.read_csv(
        "agrichain_prices.csv"
    )

    # Convert date
    df_prices["date"] = pd.to_datetime(
        df_prices["date"],
        errors="coerce"
    )

    # Convert price
    df_prices["price"] = pd.to_numeric(
        df_prices["price"],
        errors="coerce"
    )

    # Remove invalid records
    df_prices = df_prices.dropna(
        subset=[
            "date",
            "price"
        ]
    )

    print("✅ Agricultural price data loaded!")
    print(
        f"Total records: {len(df_prices)}"
    )

except Exception as e:

    print(
        f"❌ Error loading dataset: {e}"
    )

    df_prices = pd.DataFrame()


# ==========================================
# FIREBASE AUTHENTICATION
# ==========================================

@app.post("/api/auth/register")
def register_user(data: RegisterRequest):

    # Only these roles are allowed.
    # Admin accounts should be created/managed by an existing admin.
    if data.role not in ["farmer", "supplier"]:
        data.role = "farmer"

    # Basic validation
    if not data.name.strip():
        return {
            "status": "error",
            "message": "Name is required"
        }

    if not data.phone.strip():
        return {
            "status": "error",
            "message": "Phone number is required"
        }

    if len(data.password) < 6:
        return {
            "status": "error",
            "message": "Password must be at least 6 characters"
        }

    # Check whether phone already exists
    existing_users = (
        db.collection("users")
        .where("phone", "==", data.phone.strip())
        .limit(1)
        .stream()
    )

    if next(existing_users, None) is not None:
        return {
            "status": "error",
            "message": "Phone number is already registered"
        }

    # Save user in Firestore
    user_ref = db.collection("users").document()

    user_ref.set({
        "name": data.name.strip(),
        "phone": data.phone.strip(),
        "password_hash": hash_password(data.password),
        "role": data.role
    })

    return {
        "status": "success",
        "message": "Registration successful",
        "user": {
            "id": user_ref.id,
            "name": data.name.strip(),
            "phone": data.phone.strip(),
            "role": data.role
        }
    }


@app.post("/api/auth/login")
def login_user(data: LoginRequest):

    # Find user by phone
    users = (
        db.collection("users")
        .where("phone", "==", data.phone.strip())
        .limit(1)
        .stream()
    )

    user_doc = next(users, None)

    if user_doc is None:
        return {
            "status": "error",
            "message": "Invalid phone number or password"
        }

    user = user_doc.to_dict()

    # Password must be stored as a hash
    stored_hash = user.get("password_hash")

    if not stored_hash:
        return {
            "status": "error",
            "message": "This account does not have a secure password configured"
        }

    # Verify password
    if not verify_password(data.password, stored_hash):
        return {
            "status": "error",
            "message": "Invalid phone number or password"
        }

    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "id": user_doc.id,
            "name": user.get("name", ""),
            "phone": user.get("phone", ""),
            "role": user.get("role", "farmer")
        }
    }


# ==========================================
# ROOT
# ==========================================


@app.get("/")
def root():

    return {
        "status": "success",
        "message": "FarmPulse API is running",
        "total_records": len(df_prices)
    }


# ==========================================
# GET AGRICULTURAL PRODUCTS
# ==========================================

@app.get("/api/commodities")
def get_commodities():

    if df_prices.empty:

        return {
            "status": "error",
            "message": "Dataset is empty",
            "data": []
        }

    # Get unique agricultural products
    products = (
        df_prices["item"]
        .dropna()
        .unique()
        .tolist()
    )

    products = sorted(
        products,
        key=lambda x: str(x).upper()
    )

    data = []

    for product in products:

        data.append({
            "item": product
        })

    return {
        "status": "success",
        "count": len(data),
        "data": data
    }


# ==========================================
# GET MALAYSIAN STATES
# ==========================================

@app.get("/api/states")
def get_states():

    if df_prices.empty:

        return {
            "status": "error",
            "message": "Dataset is empty",
            "data": []
        }

    states = (
        df_prices["state"]
        .dropna()
        .unique()
        .tolist()
    )

    states = sorted(
        states,
        key=lambda x: str(x).upper()
    )

    return {
        "status": "success",
        "count": len(states),
        "data": states
    }


# ==========================================
# CURRENT / LATEST PRICE
# ==========================================

@app.get("/api/current-price")
def get_current_price(
    item: str,
    state: str | None = Query(
        default=None
    )
):

    if df_prices.empty:

        return {
            "status": "error",
            "data": []
        }

    # Filter product
    result = df_prices[
        df_prices["item"].str.contains(
            item,
            case=False,
            na=False
        )
    ].copy()

    # Filter state
    if state:

        result = result[
            result["state"].str.contains(
                state,
                case=False,
                na=False
            )
        ]

    # Check result
    if result.empty:

        return {
            "status": "error",
            "message": "No price data found",
            "data": []
        }

    # ==========================================
    # LATEST AVAILABLE DATE
    # ==========================================

    latest_date = result["date"].max()

    result = result[
        result["date"] == latest_date
    ].copy()


    # ==========================================
    # PRICE SUMMARY
    # ==========================================

    lowest_price = float(
        result["price"].min()
    )

    highest_price = float(
        result["price"].max()
    )

    average_price = round(
        float(result["price"].mean()),
        2
    )


    # ==========================================
    # RETURN DATA
    # ==========================================

    return {

        "status": "success",

        "item": item.upper(),

        "state": state,

        "latest_date":
            latest_date.strftime(
                "%Y-%m-%d"
            ),

        "lowest_price":
            round(
                lowest_price,
                2
            ),

        "highest_price":
            round(
                highest_price,
                2
            ),

        "average_price":
            average_price,

        "count":
            len(result),

        "data":
            result.to_dict(
                orient="records"
            )
    }

# ==========================================
# PRICE COMPARISON BY STATE
# ==========================================

@app.get("/api/price-comparison")
def price_comparison(
    item: str
):

    if df_prices.empty:

        return {
            "status": "error",
            "message": "Dataset is empty",
            "data": []
        }


    # ==========================================
    # FILTER PRODUCT
    # ==========================================

    result = df_prices[
        df_prices["item"].str.contains(
            item,
            case=False,
            na=False
        )
    ].copy()


    # ==========================================
    # CHECK PRODUCT
    # ==========================================

    if result.empty:

        return {
            "status": "error",
            "message": "No price data found",
            "data": []
        }


    # ==========================================
    # GET LATEST AVAILABLE DATE
    # ==========================================

    latest_date = result["date"].max()


    # Only use latest date
    latest_data = result[
        result["date"] == latest_date
    ].copy()


    # ==========================================
    # AVERAGE PRICE BY STATE
    # ==========================================

    comparison = (

        latest_data

        .groupby("state")["price"]

        .mean()

        .reset_index()

    )


    comparison["price"] = (
        comparison["price"]
        .round(2)
    )


    # ==========================================
    # SORT LOWEST → HIGHEST
    # ==========================================

    comparison = (
        comparison
        .sort_values(
            "price"
        )
        .reset_index(
            drop=True
        )
    )


    # ==========================================
    # RETURN RESULT
    # ==========================================

    return {

        "status": "success",

        "item":
            item.upper(),

        "latest_date":
            latest_date.strftime(
                "%Y-%m-%d"
            ),

        "count":
            len(comparison),

        "data":
            comparison.to_dict(
                orient="records"
            )

    }


# ==========================================
# HISTORICAL PRICE
# ==========================================

@app.get("/api/price-history")
def price_history(

    item: str,

    state: str | None = Query(
        default=None
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=1000
    )

):

    if df_prices.empty:

        return {
            "status": "error",
            "data": []
        }


    # ==========================================
    # FILTER PRODUCT
    # ==========================================

    result = df_prices[
        df_prices["item"].str.contains(
            item,
            case=False,
            na=False
        )
    ].copy()


    # ==========================================
    # FILTER STATE
    # ==========================================

    if state:

        result = result[
            result["state"].str.contains(
                state,
                case=False,
                na=False
            )
        ]


    # ==========================================
    # CHECK DATA
    # ==========================================

    if result.empty:

        return {

            "status": "error",

            "message":
                "No historical data found",

            "data": []

        }


    # ==========================================
    # DAILY AVERAGE PRICE
    # ==========================================

    history = (

        result

        .groupby("date")["price"]

        .mean()

        .reset_index()

        .sort_values(
            "date",
            ascending=False
        )

        .head(limit)

    )


    # Round price
    history["price"] = (
        history["price"]
        .round(2)
    )


    # ==========================================
    # RETURN
    # ==========================================

    return {

        "status": "success",

        "item": item.upper(),

        "state": state,

        "count":
            len(history),

        "data":
            history.to_dict(
                orient="records"
            )

    }


# ==========================================
# LINEAR REGRESSION PRICE PREDICTION
# ==========================================

@app.get("/api/predict-price")
def predict_price(

    item: str,

    state: str | None = Query(
        default=None
    ),

    days: int = Query(
        default=7,
        ge=1,
        le=30
    )

):

    if df_prices.empty:

        return {

            "status": "error",

            "message":
                "Price dataset is empty",

            "data": []

        }


    # ==========================================
    # FILTER PRODUCT
    # ==========================================

    result = df_prices[
        df_prices["item"].str.contains(
            item,
            case=False,
            na=False
        )
    ].copy()


    # ==========================================
    # FILTER STATE
    # ==========================================

    if state:

        result = result[
            result["state"].str.contains(
                state,
                case=False,
                na=False
            )
        ]


    # ==========================================
    # CHECK DATA
    # ==========================================

    if result.empty:

        return {

            "status": "error",

            "message":
                "No price data found",

            "data": []

        }


    # ==========================================
    # DAILY AVERAGE PRICE
    # ==========================================

    daily_price = (

        result

        .groupby("date")["price"]

        .mean()

        .reset_index()

        .sort_values("date")

    )


    # ==========================================
    # CHECK ENOUGH DATA
    # ==========================================

    if len(daily_price) < 2:

        return {

            "status": "error",

            "message":
                "Not enough historical data for prediction",

            "data": []

        }


    # Reset index
    daily_price = (
        daily_price
        .reset_index(
            drop=True
        )
    )


    # ==========================================
    # CREATE DAY NUMBER
    # ==========================================

    daily_price["day_number"] = (
        np.arange(
            len(daily_price)
        )
    )


    # ==========================================
    # X AND Y
    # ==========================================

    X = daily_price[
        ["day_number"]
    ]

    y = daily_price[
        "price"
    ]


    # ==========================================
    # CREATE MODEL
    # ==========================================

    model = LinearRegression()


    # ==========================================
    # TRAIN MODEL
    # ==========================================

    model.fit(
        X,
        y
    )


    # ==========================================
    # LAST HISTORICAL DATA
    # ==========================================

    last_day_number = (
        daily_price[
            "day_number"
        ].max()
    )

    last_date = (
        daily_price[
            "date"
        ].max()
    )


    # ==========================================
    # FUTURE DAY NUMBERS
    # ==========================================

    future_day_numbers = np.arange(

        last_day_number + 1,

        last_day_number + days + 1

    )


    # ==========================================
    # FUTURE DATES
    # ==========================================

    future_dates = pd.date_range(

        start=
            last_date
            + pd.Timedelta(
                days=1
            ),

        periods=days

    )


    # ==========================================
    # MAKE PREDICTION
    # ==========================================

    predictions = model.predict(

        future_day_numbers.reshape(
            -1,
            1
        )

    )


    # ==========================================
    # CREATE PREDICTION DATA
    # ==========================================

    prediction_data = []


    for date, prediction in zip(

        future_dates,

        predictions

    ):

        prediction_data.append({

            "date":
                date.strftime(
                    "%Y-%m-%d"
                ),

            "predicted_price":
                round(
                    max(
                        0,
                        float(
                            prediction
                        )
                    ),
                    2
                )

        })


    # ==========================================
    # MODEL INFORMATION
    # ==========================================

    slope = float(
        model.coef_[0]
    )

    intercept = float(
        model.intercept_
    )


    # ==========================================
    # RETURN PREDICTION
    # ==========================================

    return {

        "status": "success",

        "item": item.upper(),

        "state": state,

        "historical_days":
            len(daily_price),

        "prediction_days":
            days,

        "model":
            "Linear Regression",

        "slope":
            round(
                slope,
                4
            ),

        "intercept":
            round(
                intercept,
                4
            ),

        "latest_historical_date":
            last_date.strftime(
                "%Y-%m-%d"
            ),

        "data":
            prediction_data

    }