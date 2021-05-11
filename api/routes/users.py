from flask import jsonify, request, make_response
from api import app
from py2neo import NodeMatcher
from api.config.database import Database
from api.models.user import User

graph = Database().connect()


# Get the available details of a given user


@app.route('/api/user/details/', methods=['POST'])
def getUserData():
    data = request.get_json()
    userid = data['userid']
    matcher = NodeMatcher(graph)
    user = matcher.match("User", id={userid}).first()

    return make_response(jsonify(user), 200)


@app.route('/api/user/signup/', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    name = data['name']
    password = data['password']
    admin = False

    user = User(email)

    if not user.register(name, password, admin):
        data = {"message": "User is already exists"}
        return make_response(jsonify(data), 400)
    else:
        data = {"message": "Register successfully"}
        return make_response(jsonify(data), 200)


@app.route('/api/user/login/', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    user = User(email).verify_password(password)

    if not user:
        data = {"message": "Invalid login."}
        return make_response(jsonify(data), 400)
    else:
        data = {"message": "Login successfully"}
        return make_response(jsonify(data), 200)


# @app.route('/api/user/signup/', methods=['POST'])
# def signup():
#     data = request.get_json()
#     email = data['email']
#     name = data['name']
#     rawPassword = data['password']
#     salt = "5gz"
#     passwordBeforeHash = rawPassword + salt
#     # password = sha256_crypt.encrypt(passwordBeforeHash)
#     password = hashlib.sha256(passwordBeforeHash.encode()).hexdigest()
#     admin = False

#     if email == "" or name == "" or rawPassword == "":
#         data = {"message": "Data is not valid"}
#         return make_response(jsonify(data), 400)
#     else:
#         cypher = "MATCH (u:User {email: $email}) RETURN u.email AS email"
#         checkUser = graph.run(cypher, email=email)
#         if checkUser.data():
#             data = {"message": "User is already exists"}
#             return make_response(jsonify(data), 400)
#         else:
#             cypher = "CREATE (u:User {email: $email, name: $name, password: $password, admin: $admin}) RETURN u.email " \
#                      "AS email, u.name AS name, u.admin AS admin "
#             user = graph.run(cypher, email=email, name=name, password=password, admin=admin)
#             return make_response(jsonify(user.data()), 200)