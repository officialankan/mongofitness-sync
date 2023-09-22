import logging
from pymongo.database import Database


def upload_strava(db: Database, response: dict) -> (int, int):
    inserted_activities = 0
    duplicates = 0

    for activity in response:
        if not db["strava"].find_one({"id": activity["id"]}):
            db["strava"].insert_one(activity)
            logging.debug(f"inserted Strava activity with id {activity['id']}")
            inserted_activities += 1
        else:
            logging.debug(f"activity with id {activity['id']} exists in database, skipping upload")
            duplicates += 1

    logging.debug(f"inserted {inserted_activities} activities and found {duplicates} duplicates.")
    return inserted_activities, duplicates


def upload_polar(db: Database, response: dict) -> int:
    inserted_documents = 0

    for date in response:
        created = response[date]["created"]
        steps = response[date]["steps"]
        insert = {"ts": date, "steps": steps, "meta": {"created": created}}
        db["polar"].insert_one(insert)
        inserted_documents += 1

    return inserted_documents
