from data.manager import DataManager

"""
    MongoDB helpers used by the agent tools

    Methods:
        find_one(query) -> dict | None
        find_all(query, projection) -> list[dict]
        set_fields(query, fields, upsert) -> None
"""

class DbTools:
    # find one document in the hubs collection
    @staticmethod
    def find_one(query: dict) -> dict | None:
        return DataManager.hubs().find_one(query, {"_id": 0})

    # find all documents in the hubs collection
    @staticmethod
    def find_all(query: dict | None = None, projection: dict | None = None) -> list[dict]:
        return list(DataManager.hubs().find(query or {}, {"_id": 0, **(projection or {})}))

    # set fields in a document in the hubs collection
    @staticmethod
    def set_fields(query: dict, fields: dict, upsert: bool = False) -> None:
        DataManager.hubs().update_one(query, {"$set": fields}, upsert=upsert)
