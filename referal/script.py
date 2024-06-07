# from pymongo import MongoClient
# import random
# import string

# # MongoDB connection
# client = MongoClient("mongodb+srv://letzkhello:LetzKhelo2415@cluster0.zkrdbpi.mongodb.net/retryWrites=true&w=majority")
# db = client['test']
# users_collection = db['users']

# # Function to generate a 5-digit alphanumeric code in uppercase
# def generate_referral_code():
#     return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# # Function to extract first name and generate referral code
# def create_referral_code(full_name):
#     first_name = full_name.split(' ')[0].upper()
#     referral_code = f"{first_name}-{generate_referral_code()}"
#     return referral_code


# i =0

# # Update users with referral codes
# users = users_collection.find()
# for user in users:
#     full_name = user.get('name', '')
#     if full_name:
#         referral_code = create_referral_code(full_name)
#         users_collection.update_one(
#             {'_id': user['_id']},
#             {'$set': {'referral_code': referral_code}}
#         )
#         print(f"Updated user {user['_id']} with referral code {referral_code}")

# print("Referral codes added to all users.")