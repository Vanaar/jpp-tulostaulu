import os

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'mysql://<username>:<password>@127.0.0.1:3306/jpp-tulostaulu?charset=utf8mb4&binary_prefix=true'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'

    # Other configuration variables
    DEBUG = True
    DEBUG_LEVEL = 1