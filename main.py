import datetime
import logging
import os
import mdbfit
import pymongo
from dotenv import load_dotenv
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="increase verbosity, turns logging output level to debug",
                        action="store_true")
    args = parser.parse_args()

    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    load_dotenv()
    uri = os.environ.get("CONNECTION_STRING")
    database = os.environ.get("DATABASE")

    logging.basicConfig(format="%(asctime)s -- %(name)s -- [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")
    logger = logging.getLogger()
    logger.setLevel(level)

    strava = mdbfit.Strava(level=level)
    polar = mdbfit.Polar(level=level)
    client = pymongo.MongoClient(uri)

    try:
        client.admin.command("ping")
        logger.info("successfully connected to database")
    except Exception as e:
        logging.critical(e)
    db = client[database]

    # insert activities from Strava, recurse backwards until no new activities are found
    total_inserted_activities = 0
    today = datetime.datetime.today()
    timespan_delta = datetime.timedelta(weeks=10)  # longest gap of no-data

    before = today
    after = today - timespan_delta

    inserted_activities = 1
    while inserted_activities > 0:
        logger.debug(f"looking for Strava activities from "
                     f"{after.strftime('%Y-%m-%d')} to {before.strftime('%Y-%m-%d')}")
        inserted_activities = 0
        activities = strava.get_activities(before=before.timestamp(), after=after.timestamp())
        logger.debug(f"received {len(activities)} activities from Strava")
        if activities:
            for activity in activities:
                if not db["strava"].find_one({"id": activity["id"]}):
                    db["strava"].insert_one(activity)
                    inserted_activities += 1
                    logger.debug(f"inserted Strava activity with id {activity['id']}")
                    total_inserted_activities += 1
                else:
                    logger.debug(f"activity with id {activity['id']} exists in database, skipping upload")
            logger.debug(f"inserted {inserted_activities} activities")
            before -= timespan_delta
            after -= timespan_delta
        else:
            inserted_activities = 0

    logger.info(f"uploaded a total of {total_inserted_activities} activities from Strava")

    # insert daily step data from Polar
    steps = polar.get_steps()
    if steps:
        inserted_steps = 0
        updated_steps = 0

        for k in steps:
            date = datetime.datetime.strptime(k, "%Y-%m-%d")
            insert = {"date": date, "steps": steps[k], "updated": datetime.datetime.now()}
            if not db["polar"].find_one({"date": date}):
                # new date, so insert
                db["polar"].insert_one(insert)
                logger.debug(f"inserted {insert} to database")
                inserted_steps += 1
            else:
                # check if new step data is larger, if so - update
                document = db["polar"].find_one({"date": date})
                db_steps = document["steps"]
                if db_steps < steps[k]:
                    db["polar"].update_one(
                        {"date": date}, {"$set": {
                            "steps": steps[k], "updated": datetime.datetime.now()}
                        }
                    )
                    logger.debug(f"replaced {date} to {steps[k]} steps, previously had {db_steps} steps")
                    updated_steps += 1

                else:
                    logger.debug(f"not inserting {date}, {date} already exists in database and has more steps. "
                                 f"this shouldn't be happening")
        logger.info(f"inserted {inserted_steps} new dates with steps data and replaced {updated_steps} date(s)")


if __name__ == "__main__":
    main()
