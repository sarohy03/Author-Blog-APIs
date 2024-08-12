from pymongo import MongoClient
CONNECTION_STRING = "mongodb+srv://sarohy:mamdoot222@cluster0.i2pig5w.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(
    CONNECTION_STRING,
    ssl=True,
    tls=True,
    tlsAllowInvalidCertificates=False,
    tlsInsecure=False
)
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to Mongssl=true (or tls=true) if SSL is required. Example:oDB!")
except Exception as e:
    print(e)

db = client["NewDatabase"]
blog_collection = db["blogs"]
author_collection = db["authors"]
author_blog_collection = db["author_blogs"]
