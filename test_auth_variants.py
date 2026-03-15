import urllib.parse
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_auth")

def try_auth(password):
    user = "harsh1"
    cluster = "harsh1.hfifgiu.mongodb.net"
    safe_password = urllib.parse.quote_plus(password)
    uri = f"mongodb+srv://{user}:{safe_password}@{cluster}/"
    
    print(f"Trying password: {password} (Encoded: {safe_password})")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print(" SUCCESS!")
        return True
    except Exception as e:
        print(f" FAILED: {e}")
        return False

if __name__ == "__main__":
    passwords = ["#london&1234", "london&1234", "#london&1234", "<#london&1234>"]
    for p in passwords:
        if try_auth(p):
            print(f"Working password found: {p}")
            break
