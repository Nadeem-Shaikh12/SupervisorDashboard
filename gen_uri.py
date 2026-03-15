import urllib.parse

user = "harsh1"
password = "#london&1234"
cluster = "harsh1.hfifgiu.mongodb.net"

# Encode password
safe_password = urllib.parse.quote_plus(password)
uri = f"mongodb+srv://{user}:{safe_password}@{cluster}/"

print(f"Generated URI: {uri}")
