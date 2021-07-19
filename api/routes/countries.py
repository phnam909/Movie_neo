from flask import jsonify, request, make_response
from api import app
from py2neo import NodeMatcher
from flask_jwt_extended import jwt_required
from api.config.database import Database

app.secret_key = "abc"
graph = Database().connect()


@app.route('/api/admin/countries', methods=['GET'])
@jwt_required()
def getAllCountries():
    matcher = NodeMatcher(graph)
    countries = matcher.match("Country").all()
    return make_response(jsonify(countries), 200)


@app.route('/api/admin/countries', methods=['POST'])
@jwt_required()
def createCountry():
    name = request.json.get("name", None)
    query = ('CREATE (c:Country {country:$name})')
    map = {"name": name}
    try:
        graph.run(query, map)
        return make_response(jsonify({"message": "success"}), 200)
    except Exception as e:
        return (str(e))


@app.route('/api/admin/countries/<country>', methods=['DELETE'])
@jwt_required()
def deleteCountry(country):
    query = ('MATCH (c:Country {country:$country}) DETACH DELETE c')
    try:
        graph.run(query, country=country)
        return make_response(jsonify({"message": "Deleted success"}), 200)
    except Exception as e:
        return (str(e))