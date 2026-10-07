import os
from datetime import datetime, timezone
from urllib.parse import quote, unquote
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from data.seed_hubs import SEED_HUBS
from dotenv import load_dotenv

"""
    MongoDB connection manager

    Methods:
        db() -> Database: shared database handle
        hubs() -> Collection: the hubs collection
        init() -> None: create indexes and seed hubs if the collection is empty
"""


# MongoDB requires user and password to be URL-encoded (e.g. "/" as %2F); encode them so raw passwords work
def _encode_credentials(uri: str) -> str:
    scheme, sep, rest = uri.partition("://")
    credentials, at, host = rest.rpartition("@")
    if not sep or not at:
        return uri
    user, colon, password = credentials.partition(":")
    encoded = quote(unquote(user), safe="") + (colon + quote(unquote(password), safe="") if colon else "")
    return f"{scheme}://{encoded}@{host}"


class DataManager:
    _client: MongoClient | None = None

    @staticmethod
    def hub_key(city: str) -> str:
        return city.split(",")[0].strip().lower()

    @classmethod
    def db(cls) -> Database:
        if cls._client is None:
            uri = os.getenv("MONGODB_URI")

            # try to connect to MongoDB
            try:
                cls._client = MongoClient(_encode_credentials(uri), tz_aware=True, serverSelectionTimeoutMS=5000)
            except Exception as e:
                raise RuntimeError("Failed to connect to MongoDB")
        return cls._client[os.getenv("MONGODB_DB", os.getenv("DEFAULT_DB_NAME"))]

    # get the hubs collection
    @classmethod
    def hubs(cls) -> Collection:
        return cls.db()[os.getenv("HUBS_COLLECTION", "hubs")]

    # initialize the data manager
    @classmethod
    def init(cls) -> None:
        hubs = cls.hubs()
        hubs.create_index([("city_key", ASCENDING)], unique=True)

        # create indexes if the collection is empty
        now = datetime.now(timezone.utc)
        if hubs.estimated_document_count() == 0:
            hubs.insert_many(
                [{**hub, "city_key": cls.hub_key(hub["city"]), "created_at": now, "updated_at": {"location": now}} for hub in SEED_HUBS]
            )
        for hub in SEED_HUBS:
            hubs.update_one(
                {"city_key": cls.hub_key(hub["city"]), "location.latitude": {"$exists": False}},
                {"$set": {"location": hub["location"], "updated_at.location": now}},
            )
