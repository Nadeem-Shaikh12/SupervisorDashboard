import pymongo
import urllib.parse
from pprint import pprint

password = urllib.parse.quote_plus("#london&1234")
uri = f"mongodb+srv://harsh1:{password}@harsh1.hfifgiu.mongodb.net/"

client = pymongo.MongoClient(uri)
db = client["dreamvision_db"]
collection = db["inspections"]

docs = list(collection.find())
print(f"Total documents on the web (Atlas): {len(docs)}")
if docs:
    print("Latest 2 docs:")
    pprint(docs[-2:])
else:
    print("No documents found on the cloud!")
