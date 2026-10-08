import os
from datetime import datetime, timezone
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from data.seed_hubs import SEED_HUBS

"""
    MongoDB connection manager

    Methods:
        db() -> Database: shared database handle
        hubs() -> Collection: the hubs collection
        init() -> None: create indexes and seed hubs if the collection is empty
"""

class DataManager:
    _client: MongoClient | None = None

    # get the hub key
    @staticmethod
    def hub_key(city: str) -> str:
        return city.split(",")[0].strip().lower()

    # get the database
    @classmethod
    def db(cls) -> Database:
        if cls._client is None:
            # try to connect to MongoDB
            try:
                cls._client = MongoClient(os.getenv("MONGODB_URI"))
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
                [{
                    **hub,
                    "city_key": cls.hub_key(hub["city"]),
                    "created_at": now,
                    "updated_at": {"location": now},
                } for hub in SEED_HUBS]
            )
        for hub in SEED_HUBS:
            key = cls.hub_key(hub["city"])
            hubs.update_one(
                {"city_key": key, "location.latitude": {"$exists": False}},
                {"$set": {"location": hub["location"], "updated_at.location": now}},
            )
            hubs.update_one(
                {"city_key": key, "score": {"$exists": False}},
                {"$set": {"score": 0}},
            )
            hubs.update_one(
                {"city_key": key, "score": 0, "$expr": {"$eq": ["$scored_at", "$created_at"]}},
                {"$unset": {"scored_at": ""}},
            )
