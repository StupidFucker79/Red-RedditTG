from pymongo import MongoClient


def connect_to_mongodb(uri, db_name):
    try:
        client = MongoClient(uri)
        db = client[db_name]
        print("Connected to MongoDB")
        return db
    except Exception as e:
        print(f"Error: Could not connect to MongoDB.\n{e}")
        return None

def check_db(db, collection_name, url):
    collection = db[collection_name]
    result = collection.find_one({"URL": url})
    return result is not None

def insert_document(db, collection_name, document):
    try:
        collection = db[collection_name]
        collection.insert_one(document)
        logging.info(f"Document inserted into database: {document['URL']}")
    except Exception as e:
        logging.error(f"Error inserting document: {e}")


def find_documents(db, collection_name, query=None):
    try:
        collection = db[collection_name]
        if query:
            cursor = collection.find(query)
        else:
            cursor = collection.find()

        return list(cursor)
    except Exception as e:
        print(f"Error: Could not retrieve documents.\n{e}")
        return []


def get_info(db,collection_name,url):
    documents = find_documents(db, collection_name)
    urls = [doc for doc in documents if doc["URL"] == url][0]
    return urls


def get_raw_url(db,collection_name):
    documents = find_documents(db, collection_name)
    urls = [doc["URL"] for doc in documents]
    return urls
