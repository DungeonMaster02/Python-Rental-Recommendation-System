import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
def get_connect():
    conn = psycopg2.connect(host = os.getenv('host'), dbname = os.getenv('dbname'), user = os.getenv('user'), password = os.getenv('password'), port = os.getenv('port'))
    return conn

