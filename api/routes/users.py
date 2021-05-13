from flask import jsonify, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from api import app
from py2neo import NodeMatcher
from api.config.database import Database
from api.models.user import User
from datetime import timedelta

graph = Database().connect()


# Get all users

@app.route('/api/users', methods=['GET'])
@jwt_required()
def getAllUser():
    matcher = NodeMatcher(graph)
    user = matcher.match("User").limit(25).all()
    return make_response(jsonify(user), 200)


@app.route('/api/user/signup', methods=['POST'])
def signup():
    email = request.json.get("email", None)
    name = request.json.get("name", None)
    password = request.json.get("password", None)
    admin = False

    user = User(email)

    if not user.register(name, password, admin):
        data = {"message": "User is already exists"}
        return make_response(jsonify(data), 400)
    else:
        data = {"message": "Register successfully"}
        return make_response(jsonify(data), 200)


@app.route('/api/user/login', methods=['POST'])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    user = User(email).verify_password(password)

    if not user:
        data = {"message": "Invalid login."}
        return make_response(jsonify(data), 401)
    else:
        token = create_access_token(identity=email, expires_delta=timedelta(minutes=30))
        return make_response(jsonify({"token": token}), 200)


@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
