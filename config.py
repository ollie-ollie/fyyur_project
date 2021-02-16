import os

# I did not really get the comment here :)...
SECRET_KEY = os.urandom(32)

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_DATABASE_URI = 'postgres://postgres:postgres@localhost:5432/fyyur_app'
SQLALCHEMY_TRACK_MODIFICATIONS = False
