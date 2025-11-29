import uuid
from firebase_admin import firestore
from db.firebase_init import initialize_firebase


db = initialize_firebase()

def save_session(date, exercise_data)-> dict:
    mock_id = str(uuid.uuid4())[:8]
    exercise_data["id"] = mock_id
    doc_ref = db.collection("sessions").document(date)
    doc_ref.set({
        "date": date,
        "exercises": firestore.ArrayUnion([exercise_data])
    }, merge=True)
    print(f"🔥 Logged to Firebase: {exercise_data}")
    return {
    "id": mock_id,
    "message": f"✅ Successfully logged {exercise_data['sets']} sets of "
               f"{exercise_data['reps']} reps of {exercise_data['exercise']} "
               f"at {exercise_data['weight_kg']}kg."
}


def get_last_session() -> dict | None:
    """
    Fetch the most recent workout session from Firestore.
    Returns the document dict or None if no sessions exist.
    """
    sessions_ref = db.collection("sessions")
    # Order by the 'date' field descending, limit to 1
    query = sessions_ref.order_by("date", direction=firestore.Query.DESCENDING).limit(1)
    docs = query.stream()

    for doc in docs:
        return doc.to_dict()
    return None
