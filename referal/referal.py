from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
import random
import string
from datetime import datetime, timedelta


app = FastAPI()

# MongoDB connection
client = MongoClient("mongodb+srv://letzkhello:LetzKhelo2415@cluster0.zkrdbpi.mongodb.net/retryWrites=true&w=majority")
db = client['test']
users_collection = db['users']

# Function to generate a 5-digit alphanumeric code in uppercase
def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# Check if referral code exists
def referral_code_exists(referral_code):
    return users_collection.find_one({"referral_code": referral_code}) is not None


async def change_referral_code(request):
    email = request.email
    new_name = request.new_name

    # Fetch user from database
    user = users_collection.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user has already changed their referral code once
    if user.get('referral_code_changed', False):
        raise HTTPException(status_code=400, detail="Referral code can only be changed once")

    # Generate new referral code
    first_name = new_name.split(' ')[0].upper()
    new_referral_code = f"{first_name}-{generate_referral_code()}"

    # Ensure the new referral code does not already exist
    while referral_code_exists(new_referral_code):
        new_referral_code = f"{first_name}-{generate_referral_code()}"

    # Update the user's referral code and set the flag
    users_collection.update_one(
        {"email": email},
        {"$set": {"referral_code": new_referral_code, "referral_code_changed": True}}
    )

    return {"message": "Referral code updated successfully", "new_referral_code": new_referral_code}

async def apply_referral(request):
    user_email = request.user_email
    referral_code = request.referral_code
    competition_fees = request.competition_fees
    sport_referred_to = request.sport_referred_to  # Added field

    # Fetch the referred user and the referrer from the database
    referred_user = users_collection.find_one({"email": user_email})
    referrer_user = users_collection.find_one({"referral_code": referral_code})
    
    if not referred_user:
        raise HTTPException(status_code=404, detail="Referred user not found")

    if not referrer_user:
        raise HTTPException(status_code=404, detail="Invalid referral code")

    # Calculate the 5% credit
    credit_amount = competition_fees * 0.05
    unlock_date = datetime.utcnow() + timedelta(days=30)

    # Update the referred user's wallet balance, referral credits, and history
    users_collection.update_one(
        {"email": user_email},
        {"$push": {
            "referral_credits": {"amount": credit_amount, "unlock_date": unlock_date},
            "wallet_history": {
                "change": credit_amount,
                "timestamp": datetime.utcnow(),
                "description": f"Amount of {credit_amount} is deducted from com fees of {sport_referred_to} from referral code {referral_code}",
                "sportReferredTo": sport_referred_to  # Added field
            }
         }}
    )

    # Update the referrer's wallet balance, referral credits, and history
    users_collection.update_one(
        {"email": referrer_user["email"]},
        {"$inc": {"wallet_balance": credit_amount},
         "$push": {
            "referral_credits": {"amount": credit_amount, "unlock_date": unlock_date},
            "wallet_history": {
                "change": credit_amount,
                "timestamp": datetime.utcnow(),
                "description": f"Credit for referring {user_email}",
                "sportReferredTo": sport_referred_to  # Added field
            }
         }}
    )

    # Track the referral in the referrer's referrals list
    users_collection.update_one(
        {"email": referrer_user["email"]},
        {"$push": {"referrals": {"referred_user_email": user_email, "timestamp": datetime.utcnow(), "sportReferredTo": sport_referred_to}}}
    )

    return {"message": "Referral applied successfully", "credit_amount": credit_amount}

async def redeem_coins(request):
    email = request.email
    redeem_amount = request.amount
    sport_redeemed_to = request.sport_redeemed_to  # Added field

    # Fetch user from the database
    user = users_collection.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wallet_balance = user.get('wallet_balance', 0)
    referral_credits = user.get('referral_credits', [])

    if wallet_balance < redeem_amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")

    # Calculate the total eligible credits
    total_eligible_credits = sum(
        credit['amount'] for credit in referral_credits if credit['unlock_date'] <= datetime.utcnow()
    )

    if total_eligible_credits < redeem_amount:
        raise HTTPException(status_code=400, detail="Insufficient eligible credits for redemption")

    # Deduct the redeemed amount from the user's wallet balance
    users_collection.update_one(
        {"email": email},
        {"$inc": {"wallet_balance": -redeem_amount},
         "$push": {
             "wallet_history": {
                 "change": -redeem_amount,
                 "timestamp": datetime.utcnow(),
                 "description": f"Redemption for {sport_redeemed_to}",
                 "sportRedeemedTo": sport_redeemed_to  # Added field
             }
         }}
    )

    return {"message": "Coins redeemed successfully", "redeemed_amount": redeem_amount}



async def check_referral_code(request):
    referral_code = request.referral_code

    # Check if the referral code exists
    referrer_user = users_collection.find_one({"referral_code": referral_code})
    
    if not referrer_user:
        raise HTTPException(status_code=404, detail="Invalid referral code")

    return {"message": "Referral code is valid"}