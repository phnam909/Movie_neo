from flask import jsonify, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from api import app
from py2neo import NodeMatcher
from api.config.database import Database
from api.models.user import User
from datetime import timedelta
from passlib.hash import bcrypt
from flask_cors import CORS, cross_origin

graph = Database().connect()


# ===================== Admin router  ============================

# Get all users admin

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def getAllUserAdmin():
    matcher = NodeMatcher(graph)
    user = matcher.match("User").all()
    # counter = graph.run("MATCH (u:User) RETURN count(u)").evaluate()
    resp = make_response(jsonify(user), 200)
    # resp.headers['X-Total-Count'] = counter
    return resp


@app.route('/api/admin/users/<uid>', methods=['GET'])
@jwt_required()
def getUserData(uid):
    matcher = NodeMatcher(graph)
    user = matcher.match("User", id=int(uid)).first()
    resp = make_response(jsonify(user), 200)
    return resp


@app.route('/api/admin/users/<username>', methods=['DELETE'])
@jwt_required()
def deleteUser(username):
    query = ('MATCH (g:User {username:$username}) DETACH DELETE g')
    try:
        graph.run(query, username=username)
        return make_response(jsonify({"message": "Deleted success"}), 200)
    except Exception as e:
        return (str(e))

@app.route('/api/admin/users/char-user', methods=['GET'])
# @jwt_required()
def userWithNumberOfRating():
    dataUser = graph.run('MATCH (u:User) RETURN u.username AS username, size((u)-[:RATED]->()) AS count ORDER BY count LIMIT 5')

    return jsonify(dataUser.data())

@app.route('/api/admin/users/char-movie', methods=['GET'])
# @jwt_required()
def movieWithNumberOfRating():
    dataMovie = graph.run('MATCH (m:Movie) RETURN m.title AS title, size(()-[:RATED]->(m)) AS count ORDER BY count DESC LIMIT 5')

    return jsonify(dataMovie.data())

@app.route('/api/admin/users/char-avg', methods=['GET'])
# @jwt_required()
def movieWithAvgRating():
    dataMovie = graph.run('MATCH (u:User)-[r:RATED]->(m:Movie) RETURN m.title AS title, avg(r.rating) AS avg ORDER BY avg DESC LIMIT 5')

    return jsonify(dataMovie.data())

# ================================================================


@app.route('/api/register', methods=['POST'])
def register():
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
        token = create_access_token(
            identity=username, expires_delta=timedelta(minutes=30))
        return make_response(jsonify({"token": token}), 200)


@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    user = User(username).verify_password(password)
    userInfo = User(username).find_by_username()
    isAdmin = userInfo["admin"]
    if not user:
        data = {"message": "Invalid login."}
        return make_response(jsonify(data), 400)
    else:
        if not isAdmin:
            token = create_access_token(
                identity=username, expires_delta=timedelta(minutes=120))
            return make_response(jsonify({"token": token}), 200)
        else:
            token = create_access_token(
                identity=username + "-admin", expires_delta=timedelta(minutes=120))
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


@app.route('/api/profile', methods=['POST'])
@jwt_required()
def profile():
    username = request.json.get("username", None)
    query = (
        'MATCH (u:User {username: $username}) RETURN u')
    genre = graph.run(query, username=username)
    gen = genre.evaluate()
    if gen:
        return make_response(jsonify(gen), 200)
    else:
        return make_response(jsonify({"message": "Opps! Something wrong"}), 404)


@app.route('/api/change-password', methods=['POST'])
@jwt_required()
def change_password():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    query = (
        'MATCH (p:User {username: $username}) SET p.password = $password RETURN p')
    genre = graph.run(query, username=username,
                      password=bcrypt.encrypt(password))
    if genre:
        return make_response(jsonify({"message": "Ok"}), 200)
    else:
        return make_response(jsonify({"message": "Opps! Something wrong"}), 404)

@app.route('/api/change-profile', methods=['POST'])
@jwt_required()
def change_profile():
    username = request.json.get("username", None)
    name = request.json.get("name", None)

    query = (
        'MATCH (p:User {username: $username}) SET p.name = $name RETURN p')
    genre = graph.run(query, username=username, name=name)
    if genre:
        return make_response(jsonify({"message": "Ok"}), 200)
    else:
        return make_response(jsonify({"message": "Opps! Something wrong"}), 404)

####### User #######

# Get the submitted ratings by a given user


@app.route('/api/user/ratings/<userId>')
def getUserRatings(userId):
    ratings = graph.run(
        'MATCH (u:User {id: $userId})-[r:RATED ]->(movies) RETURN movies.title AS movie, r.rating AS rating',
        userId=userId)

    return jsonify(ratings.data())


# Get the submitted tags by a given user


@app.route('/api/user/tags/<userId>')
def getUserTags(userId):
    tags = graph.run(
        'MATCH (u:User {id: $userId})-[t:TAGGED ]->(movies) RETURN movies.title AS title, t.tag AS tag', userId=userId)

    return jsonify(tags.data())


# Get the average rating by a given user


@app.route('/api/user/average-rating/<userId>')
def getUserAverageRating(userId):
    avg = graph.run(
        'MATCH (u: User {id: $userId})-[r:RATED]->(m:Movie) RETURN u.id AS user, avg(toFloat(r.rating)) AS '
        'averageRating', userId=userId)

    return jsonify(avg.data())

