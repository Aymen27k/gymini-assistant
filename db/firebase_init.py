import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


# 1. Initialize Firebase (Run this once at the start of your app)
def initialize_firebase():
    """Initializes the Firebase Admin SDK using a local key"""
    # Check if already initialized to avoid errors during re-runs
    if not firebase_admin._apps:
        cred = credentials.Certificate("db/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    
    # 2. Get the Database Client
    db = firestore.client()
    print("Firebase Firestore initialized successfully.")
    return db
