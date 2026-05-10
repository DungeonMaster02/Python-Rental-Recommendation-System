import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path

try:
    from path_config import ENV_FILE
except ImportError:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
else:
    load_dotenv(ENV_FILE)


def get_connect():
    conn = psycopg2.connect(host = os.getenv('host'), dbname = os.getenv('dbname'), user = os.getenv('user'), password = os.getenv('password'), port = os.getenv('port'))
    return conn
