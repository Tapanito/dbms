from movielens import *
from peewee import *
from playhouse.shortcuts import *
from pymongo import *
from bson.objectid import ObjectId
import re
from datetime import datetime
import datetime

MOVIE = "movies"
USER = "users"
RATING = "ratings"

def migrate():
  migrate_user()
  migrate_movie()
  migrate_rating()
  query_1()

def migrate_user():
  drop_collection(USER)
  count = 0
  for user in Users.select():
    userDict = model_to_dict(user)
    userDict['legacyId'] = userDict.pop('id', None)
    insert_to_mongo(userDict, USER)
    count += 1
  print("Users migrated " + str(count))

def migrate_movie():
  drop_collection(MOVIE)
  count = 0
  for movie in Movies.select():
    movieDict = model_to_dict(movie)
    #init the genre list
    movieDict['genre'] = []
    # remove the id field, mongo will generate it's own but keep the legacyId
    movieDict['legacyId'] = movieDict.pop('id', None)
    try:
      movieDict['release_date'] = datetime.strptime(movieDict['release_date'], '%d-%b-%Y')
    except:
      date = get_movie_date(movieDict['title'])
      if date is not None:
        movieDict['release_date'] = datetime.datetime(int(date), 1, 1, 0, 0)
      else:
        movieDict['release_date'] = None
    # add related genres
    for genre in movie.genres:
      movieDict['genre'] += [genre.genre.genre]
    insert_to_mongo(movieDict, MOVIE)
    count += 1
  print("Movies migrated " + str(count))

def get_movie_date(title):
  match = re.search('\([0-9]{4}\)', title)
  if match is not None:
    date = re.search('[0-9]{4}', match.group())
    return None if date is None else date.group()

def migrate_rating():
  drop_collection(RATING)
  count = 0
  movies = get_collection_items(MOVIE)
  for movie in movies:
    dicts = []
    # find all ratings for the movie
    ratings = Ratings.select().where(Ratings.movie == movie['legacyId'])
    for rating in ratings:
      ratingDict = model_to_dict(rating)
      ratingDict['legacyId'] = ratingDict.pop('id', None)
      # find the user who gave the rating
      user = find_item(USER, 'legacyId', rating.user.id)
      if user is not None:
        ratingDict['user'] = ObjectId(str(user['_id']))
        ratingDict['movie'] = ObjectId(str(movie['_id']))
        dicts.append(ratingDict.copy())
        count += 1
      else:
        print("User not found")
    insert_many(RATING, dicts)
    print("Count: " + str(count))
  print("Ratings migrated " + str(count))

def connect_to_mongo():
  client = MongoClient("mongodb://vt50:abcvt50354@mongo-server-1/vt50")
  return client.vt50

def insert_to_mongo(item, collection):
  # connect to mongo
  database = connect_to_mongo()
  database[collection].insert(item)

def get_collection_items(collection):
  database = connect_to_mongo()
  return database[collection].find()

def find_item(collection, key, value):
  database = connect_to_mongo()
  return database[collection].find_one({key : value})

def insert_many(collection, item_list):
  database = connect_to_mongo()
  database[collection].insert_many(item_list)


def drop_collection(collection):
  database = connect_to_mongo();
  database[collection].drop()

# Find the top rated movie of all time
def query_1():
  database = connect_to_mongo()
  pipeline = [
    {"$group": {"_id":"$movie", "rating":{"$avg":"$rating"}}},
    {"$sort":{"rating": -1}}
  ]
  result = database[RATING].aggregate(pipeline)
  # get the top rated movie
  item = result.next()
  # find the movie entry
  return database[MOVIE].find_one({"_id": item['_id']})

# Find all the movie released in a given year
def query_2(year):
  database = connect_to_mongo()
  start = datetime.datetime(int(year), 1, 1, 0, 0)
  end = datetime.datetime(int(year) + 1  , 1, 1, 0, 0)
  movies = database[MOVIE].find({"release_date" : {"$gte" : start, "$lt":end}})
  return movies

# find the most popular movies of a given year
# Movie is popular if it has more than 500 ratings
def query_3(year):
  database = connect_to_mongo()
  topRated = []
  for movie in query_2(year):
    count = database[RATING].count({"movie" : movie["_id"]})
    print("Count: " + str(count))
    if count > 500:
      topRated.append(movie.copy())
  return topRated

# find the x most rated movies of all time
def query_4(count):
  database = connect_to_mongo()
  pipeline = [
    {"$group": {"_id":"$movie", "rating":{"$avg":"$rating"}, "count" : {"$sum":1}}},
    {"$sort":{"count": -1}}
  ]
  result = database[RATING].aggregate(pipeline)
  i = 0
  movies = []
  for item in result:
    if i >= count:
      break
    movies.append(find_item(MOVIE, "_id", item["_id"]))
    i+=1
  return movies

# find the most popular movie by occupation
def query_5(occupation = None):
  database = connect_to_mongo()
  users = database[USER].find({"occupation" : occupation})
  movies = []
  for user in users:
    result = database[RATING].find({"user": user['_id']})
    for item in result:
      if item['movie'] not in movies:
          movies.append(item['movie'])
  topMovie = None
  for movie in movies:
    pipeline = [
      {"$match" : {"movie": movie}},
      {"$group": {"_id":"$movie", "rating":{"$avg":"$rating"}, "count" : {"$sum":1}}},
      {"$sort":{"count": -1}}
    ]
    result = database[RATING].aggregate(pipeline)
    tmp = result.next()
    if topMovie is None:
      topMovie = tmp
    else:
      if topMovie['rating'] < tmp['rating']:
        topMovie = tmp

  return database[MOVIE].find({'_id': topMovie['_id']})


if __name__  == "__main__":
	migrate()

