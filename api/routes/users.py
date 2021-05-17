from flask import jsonify, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from api import app
from py2neo import NodeMatcher
from api.config.database import Database
from api.models.user import User
from datetime import timedelta

graph = Database().connect()


# ===================== Admin router  ============================

# Get all users admin

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def getAllUserAdmin():
    matcher = NodeMatcher(graph)
    user = matcher.match("User").all()
    counter = graph.run("MATCH (u:User) RETURN count(u)").evaluate()
    resp = make_response(jsonify(user), 200)
    resp.headers['X-Total-Count'] = counter
    return resp


@app.route('/api/admin/users/<uid>', methods=['GET'])
@jwt_required()
def getUserData(uid):
    matcher = NodeMatcher(graph)
    user = matcher.match("User", id=int(uid)).first()
    resp = make_response(jsonify(user), 200)
    return resp


# ================================================================


@app.route('/api/signup', methods=['POST'])
def signup():
    username = request.json.get("username", None)
    email = request.json.get("email", None)
    name = request.json.get("name", None)
    password = request.json.get("password", None)
    admin = False

    user = User(username)

    if not user.register(name, password, admin, email):
        data = {"message": "User is already exists"}
        return make_response(jsonify(data), 400)
    else:
        data = {"message": "Register successfully"}
        return make_response(jsonify(data), 200)


@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    user = User(username).verify_password(password)

    if not user:
        data = {"message": "Invalid login."}
        return make_response(jsonify(data), 401)
    else:
        token = create_access_token(identity=username, expires_delta=timedelta(minutes=30))
        return make_response(jsonify({"token": token}), 200)


@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


@app.route('/admin/auth', methods=['GET'])
@jwt_required()
def auth():
    resp = make_response(jsonify({"message": "Authenticated"}), 200)
    return resp
