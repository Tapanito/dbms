from peewee import *

database = MySQLDatabase('movielens', **{'user': 'vt50', 'password': 'abcvt50354', 'host': 'mysql-server-1'})

class UnknownField(object):
    pass

class BaseModel(Model):
    class Meta:
        database = database

class Genres(BaseModel):
    genre = CharField(null=True)

    class Meta:
        db_table = 'genres'

class Movies(BaseModel):
    imdburl = CharField(db_column='IMDBURL', null=True)
    release_date = CharField(null=True)
    title = CharField(null=True)
    video = CharField(null=True)

    class Meta:
        db_table = 'movies'

class MovieGenres(BaseModel):
    genre = ForeignKeyField(db_column='genre', rel_model=Genres, to_field='id')
    movie = ForeignKeyField(db_column='movie', rel_model=Movies, to_field='id', related_name='genres')

    class Meta:
        db_table = 'movie_genres'
        indexes = (
            (('movie', 'genre'), True),
        )
        primary_key = CompositeKey('genre', 'movie')

class Users(BaseModel):
    age = IntegerField(null=True)
    gender = CharField(null=True)
    occupation = CharField(null=True)
    zip_code = CharField(null=True)

    class Meta:
        db_table = 'users'

class Ratings(BaseModel):
    movie = ForeignKeyField(db_column='movie', rel_model=Movies, to_field='id', related_name='ratings')
    rating = IntegerField(null=True)
    timestamp = IntegerField(null=True)
    user = ForeignKeyField(db_column='user', rel_model=Users, to_field='id')

    class Meta:
        db_table = 'ratings'
        indexes = (
            (('user', 'movie'), True),
        )
        primary_key = CompositeKey('movie', 'user')

