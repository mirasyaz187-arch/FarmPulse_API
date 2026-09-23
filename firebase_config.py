import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    firebase_json = os.environ["FIREBASE_CREDENTIALS_JSON"]
    firebase_secrets = json.loads(firebase_json)

    cred = credentials.Certificate(firebase_secrets)
    firebase_admin.initialize_app(cred)

db = firestore.client()
