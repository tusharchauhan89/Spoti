from flask import Blueprint, request, jsonify
from models import db, User
from werkzeug.security import check_password_hash
import jwt
import datetime
from flask_cors import CORS

auth_bp = Blueprint('auth', __name__)
CORS(auth_bp)

SECRET_KEY = 'your_secret_key'  # Same as in app config


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid username or password'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, SECRET_KEY, algorithm='HS256')

    return jsonify({'token': token, 'user_id': user.id, 'username': user.username}), 200
