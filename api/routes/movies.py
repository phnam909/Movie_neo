from flask import jsonify, request, make_response, flash
from api import app
from py2neo import Graph, Node, NodeMatcher
from api.config.database import Database
import calendar
import time
import uuid

app.secret_key = "abc"
graph = Database().connect()

# Get the available details of a given movie


@app.route('/api/movie/details/', methods=['POST'])
def getMovieData():
    data = request.get_json()
    title = data['title']
    matcher = NodeMatcher(graph)
    movie = matcher.match("Movie", title={title}).first()
    if not movie:
        return make_response(jsonify({"message": "Movie not found"}), 404)
    else:
        return make_response(jsonify(movie), 404)

# Get the genres associated with a given movie


@app.route('/api/movie/genres/', methods=['POST'])
def getMovieGenres():
    data = request.get_json()
    title = data['title']
    genres = graph.run(
        'MATCH (genres)-[:IS_GENRE_OF]->(m:Movie {title: $title}) RETURN genres', title=title)

    return jsonify(list(genres))

# Get the submitted ratings of a given movie


@app.route('/api/movie/ratings/<title>')
def getMovieRatings(title):
    ratings = graph.run(
        'MATCH (u: User)-[r:RATED]->(m:Movie {title: $title}) RETURN u.id AS user, r.rating AS rating', title=title)

    return jsonify(ratings.data())

# Get the submitted tags of a given movie


@app.route('/api/movie/tags/<title>')
def getMovieTags(title):
    tags = graph.run(
        'MATCH (u: User)-[t:TAGGED]->(m:Movie {title: $title}) RETURN u.id AS user, t.tag AS tag', title=title)

    return jsonify(tags.data())


# Get list of movies from a given year
@app.route('/api/movie/year/<year>')
def getMoviesByYear(year):
    movies = graph.run(
        'MATCH (m:Movie) WHERE m.year = $year RETURN m.title AS title, m.year AS year', year=year)

    return jsonify(movies.data())

# Get the average rating for a given movie


@app.route('/api/movie/average-rating/<title>')
def getMovieAverageRating(title):
    avg = graph.run(
        'MATCH (u: User)-[r:RATED]->(m:Movie {title: $title}) RETURN m.title AS title, avg(toFloat(r.rating)) AS '
        'averageRating', title=title)

    return jsonify(avg.data())

####### Top #######

# Get top N highest rated movies
        

@app.route('/api/top/movie/top-n/<n>')
def getMovieTopN(n):
    mvs = graph.run(
        'MATCH (u: User )-[r:RATED]->(m:Movie) RETURN m.title AS title, avg(r.rating) AS averageRating order by '
        'averageRating desc limit toInteger($n)', n=n)

    return jsonify(mvs.data())

# Get top N most rated movies


@app.route('/api/top/movie/n-most-rated/<n>')
def getMovieNMostRated(n):
    mvs = graph.run(
        'MATCH (u: User)-[r:RATED]->(m:Movie) RETURN m.title AS title, count(r.rating) as NumberOfRatings order by '
        'NumberOfRatings desc limit toInteger($n)', n=n)

    return jsonify(mvs.data())

####### User #######

# Get the submitted ratings by a given user


@app.route('/api/user/ratings/<userId>')
def getUserRatings(userId):
    ratings = graph.run(
        'MATCH (u:User {id: $userId})-[r:RATED ]->(movies) RETURN movies.title AS movie, r.rating AS rating', userId=userId)

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

# Recommender Enginer

# Content based


@app.route('/api/rec_engine/content/', methods=['POST'])
def getRecContent():
    data = request.get_json()
    title = data['title']
    n = data['n']
    avg = graph.run('MATCH (m:Movie)<-[:IS_GENRE_OF]-(g:Genre)-[:IS_GENRE_OF]->(rec:Movie) '
                    'WHERE m.title = $title '
                    'WITH rec, COLLECT(g.name) AS genres, COUNT(*) AS numberOfSharedGenres '
                    'RETURN rec.title as title, genres, numberOfSharedGenres '
                    'ORDER BY numberOfSharedGenres DESC LIMIT toInteger($n);', title=title, n=n)

    return jsonify(avg.data())

# Collaborative Filtering


@app.route('/api/rec_engine/collab/', methods=['POST'])
def getRecCollab():
    data = request.get_json()
    userid = data['userid']
    n = data['n']
    rec = graph.run('MATCH (u1:User {id:$userid})-[r:RATED]->(m:Movie) '
                    'WITH u1, avg(r.rating) AS u1_mean '
                    'MATCH (u1)-[r1:RATED]->(m:Movie)<-[r2:RATED]-(u2) '
                    'WITH u1, u1_mean, u2, COLLECT({r1: r1, r2: r2}) AS ratings WHERE size(ratings) > 10 '
                    'MATCH (u2)-[r:RATED]->(m:Movie) '
                    'WITH u1, u1_mean, u2, avg(r.rating) AS u2_mean, ratings '
                    'UNWIND ratings AS r '
                    'WITH sum( (r.r1.rating-u1_mean) * (r.r2.rating-u2_mean) ) AS nom, '
                    'sqrt( sum( (r.r1.rating - u1_mean)^2) * sum( (r.r2.rating - u2_mean) ^2)) AS denom, u1, '
                    'u2 WHERE denom <> 0 '
                    'WITH u1, u2, nom/denom AS pearson '
                    'ORDER BY pearson DESC LIMIT 10 '
                    'MATCH (u2)-[r:RATED]->(m:Movie) WHERE NOT EXISTS( (u1)-[:RATED]->(m) ) '
                    'RETURN m.title AS title, SUM( pearson * r.rating) AS score '
                    'ORDER BY score DESC LIMIT toInteger($n);', userid=userid, n=n)

    return jsonify(rec.data())

# Create 
@app.route('/api/movie/add_movie', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        id = str(uuid.uuid4())
        title = request.form['title']
        poster = request.form['poster']
        content = request.form['content']
        duration = request.form['duration']
        language = request.form['language']
        country = request.form['country']
        genres = request.form['genres']
        year = request.form['year']
        actors = request.form['actors']
        slug = request.form['slug']
        timestamp = calendar.timegm(time.gmtime())
        print(timestamp)
        movie = ' MERGE (u:Movie {id: $id,title: $title,poster: $poster,content: $content, duration: $duration, language: $language,slug: $slug,timestamp: $timestamp})'
        map={"id" : id,"title" : title, "poster": poster, "content": content, "duration": duration, "language": language,"slug": slug, "timestamp": timestamp}

        try:
            graph.run(movie,map)
            # return jsonify(result.data())
            print(id)
            print(country)

            ctry = 'MERGE (c:Country {country: $country})'
            map = {"country": country}  
            graph.run(ctry,map)

            relationship = 'MATCH (m:Movie) , (c:Country) WHERE m.id = $id and c.country = $country MERGE (m)<-[r:HAS]-(c) RETURN m,c'
            map = {"id":id ,"country" : country}    
            graph.run(relationship,map) 

            # format string before create
            genres = [x.strip() for x in genres.split(',')]
            genres = [genre.capitalize() for genre in genres]
            for gen in genres:

                gnr = 'MERGE (g:Genre {name: $gen})'   
                map = {"gen": gen}
                graph.run(gnr,map)

                relationship = 'MATCH (m:Movie) , (g:Genre) WHERE m.id = $id and g.name = $gen MERGE (m)<-[r:IS_GENRE_OF]-(g) RETURN m,g'
                map = {"id":id ,"gen" : gen}
                print(map)    
                graph.run(relationship,map) 
            
            year_query = 'MERGE (y:Year {year: $year})'
            map = {"year": year}
            graph.run(year_query,map)

            relationship = 'MATCH (m:Movie) , (y:Year) WHERE m.id = $id and y.year = $year MERGE (m)-[r:PUBLISHED_IN]->(y) RETURN m,y'
            map= {"id" : id, "year": year}
            graph.run(relationship,map) 
            
            actors = [x.strip() for x in actors.split(',')]
            actors = [actor.title() for actor in actors]
            for actor in actors:
                print(actor)
                acts = 'MERGE (g:Actor {name: $actor})'   
                map = {"actor": actor}
                graph.run(acts,map)

                relationship = 'MATCH (m:Movie) , (a: Actor) WHERE m.id = $id and a.name = $actor MERGE (a)-[r:ACTION_IN]->(m) RETURN m,a'
                map = {"id":id ,"actor" : actor}
                print(map)    
                graph.run(relationship,map) 

            flash('add success')
            return make_response(jsonify({"message": "success"}), 200)
        except Exception as e:
            flash('Movie existed')
            return (str(e))

# Show All Movie 
@app.route('/api/movie/all_movie',methods=['GET']) 
def show_all_movie():
    query = 'MATCH (m:Movie) RETURN m ORDER BY m.timestamp DESC'
    movie = graph.run(query)
    return jsonify(movie.data())

# Update Movie
@app.route('/api/movie/update/<slug>',methods=['GET','PUT'])
def update_movie(slug):
    if request.method == 'GET': 
       
        query = 'MATCH (m:Movie) WHERE m.slug = $slug RETURN m as Movie'
        movie = graph.run(query,slug = slug)
        check = movie.data()

        if not check:
            return make_response(jsonify({"message": "Not Found"}), 404)

        return jsonify(check)
    if request.method == 'PUT':
        
        query = 'MATCH (m:Movie) WHERE m.slug = $slug RETURN m as Movie'
        movie = graph.run(query,slug = slug)


        return 'update'
# Delete Movie