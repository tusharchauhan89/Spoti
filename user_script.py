# print_users.py

from db import db
from models import User
from flask import Flask

# Create the Flask app context if needed
app = Flask(__name__)
app.app_context().push()

# Query and print all users
users = User.query.all()

if users:
    print("📋 Registered Users:\n")
    for user in users:
        print(f"🆔 ID: {user.id} | 👤 Username: {user.username} | 📧 Email: {user.email}")
else:
    print("❌ No users found in the database.")
