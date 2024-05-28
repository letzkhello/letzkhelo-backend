#mongo db
from pymongo import MongoClient

from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from typing import Any


client = MongoClient("mongodb+srv://letzkhello:LetzKhelo2415@cluster0.zkrdbpi.mongodb.net/retryWrites=true&w=majority")
db = client["test"]
users_collection = db["users"]
competitions_collection = db["addsports"]
bookings_collection = db["bookforcompetetions"]

def custom_jsonable_encoder(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if hasattr(obj, "__dict__"):
        return vars(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def get_users_by_event_name(event_name):
    return users_collection.find({"event_name": event_name})

async def get_competitions(request):
    final_data = []
    data = competitions_collection.find({})
    for doc in data:
        final_data.append(doc["sportName"])
    print("competitions\n\n")
    print(request)
    return final_data

async def has_access_for_competition(request):
    user_email = request.email
    user = users_collection.find_one({"email": user_email})
    try:
        if user and user["role"] == "superAdmin":
            return True
        
        if user and request.sportName in user["sportAccess"]:
            return True
    except:
        return False
    
# superadmin can provide admin access to a competition to a user by adding his sportsName in his sportAccess array
async def provide_admin_access(request):
    superadmin_email = request.superadmin_email
    user_email = request.email
    
    try:
        # check if superadmin_email is a superadmin
        superadmin = users_collection.find_one({"email": superadmin_email})

        email_access = []
        if superadmin and superadmin["role"] == "superAdmin":
            res = users_collection.find_one({"email": user_email})
            print("\n\n\n",res)
            if "sportAccess" in res:
                user_current_sport_access = res["sportAccess"]
                for sport in user_current_sport_access:
                    email_access.append(sport)

            email_access.append(request.sportName)
            print(email_access)
            user = users_collection.update_one({"email": user_email}, {"$set": {"sportAccess": email_access}})
            return True
    except:
        return False

async def get_registered_users_by_sport_name(request):
    sport_name = request.sportName
    user_email = request.email
    # check if user has access to the sport
    try: 
        user = users_collection.find_one({"email": user_email})
        res = {}
        print(user)
        if user and sport_name in user["sportAccess"] or user["role"] == "superAdmin":
            users = bookings_collection.find({"sportName": sport_name})
            users_list = list(users)  # Convert cursor to list
            serialized_users = jsonable_encoder(users_list, custom_encoder={ObjectId: str})
            return serialized_users
    except:
        print("error")
        return False

