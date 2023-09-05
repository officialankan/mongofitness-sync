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


def upload_polar(db: Database, response: dict) -> (int, int):
    inserted_steps = 0
    updated_steps = 0

    for date in response:
        created = response[date]["created"]
        steps = response[date]["steps"]
        insert = {"ts": date, "steps": steps, "meta": {"created": created}}
        if not db["polar"].find_one({"ts": date}):
            # new date, so insert
            db["polar"].insert_one(insert)
            logging.debug(f"inserted {insert} to database")
            inserted_steps += 1
        else:
            # check if new step data is larger, if so - update
            document = db["polar"].find_one({"ts": date})
            db_steps = document["steps"]
            if db_steps < steps:
                db["polar"].update_one(
                    {"ts": date}, {"$set": {
                        "steps": steps, "meta.created": created}
                    }
                )
                logging.debug(f"replaced {date} to {steps} steps, previously had {db_steps} steps")
                updated_steps += 1
            else:
                logging.debug(f"not inserting {date}, {date} already exists in database and has more steps. "
                                f"this shouldn't be happening")
    logging.info(f"inserted {inserted_steps} new dates with steps data and replaced {updated_steps} date(s)")

    return inserted_steps, updated_steps
