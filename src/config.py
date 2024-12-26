import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
    TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
    MONGODB_URI = os.getenv('MONGODB_URI')
    PROXYMESH_USERNAME = os.getenv('PROXYMESH_USERNAME')
    PROXYMESH_PASSWORD = os.getenv('PROXYMESH_PASSWORD')
    PROXY_LIST = [
        "us-wa.proxymesh.com:31280",
        "us-ny.proxymesh.com:31280",
        "us-fl.proxymesh.com:31280",
        "us-ca.proxymesh.com:31280",
        "us-il.proxymesh.com:31280"
    ]