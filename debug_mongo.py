import os
import sys
from pymongo import MongoClient
import urllib.parse

# Let's test two forms of the password - one with brackets and one without, to see which connects.
raw_password_without_brackets = "#london&1234"
raw_password_with_brackets = "<#london&1234>"

encoded_no_brackets = urllib.parse.quote_plus(raw_password_without_brackets)
encoded_with_brackets = urllib.parse.quote_plus(raw_password_with_brackets)

uri_no_brackets = f"mongodb+srv://harsh1:{encoded_no_brackets}@harsh1.hfifgiu.mongodb.net/"
uri_with_brackets = f"mongodb+srv://harsh1:{encoded_with_brackets}@harsh1.hfifgiu.mongodb.net/"

def test_connection(uri, label):
    print(f"Testing {label} connection...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"SUCCESS with {label}!")
        return True
    except Exception as e:
        print(f"FAILED with {label}: {e}")
        return False

success_no = test_connection(uri_no_brackets, "Without Brackets")
success_with = test_connection(uri_with_brackets, "With Brackets")

if not success_no and not success_with:
    print("Both connection attempts failed. The IP might need to be whitelisted in Atlas.")
