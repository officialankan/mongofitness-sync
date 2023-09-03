import datetime
import logging
import os
import mdbfit
import pymongo
from dotenv import load_dotenv
import argparse
import time


def main():
    parser = argparse.ArgumentParser(description="Sync Strava and Polar data to MongoDB.")
    
    parser.add_argument("--strava", help="sync Strava", action="store_true")
    parser.add_argument("--polar", help="sync Polar", action="store_true")
    parser.add_argument("--history", nargs=1, type=str, help="historical sync with Strava from HISTORY date in YYYY-MM-dd format")
    parser.add_argument("--verbose", help="increase verbosity, turns logging output level to debug",
                        action="store_true")
    args = parser.parse_args()

    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format="%(asctime)s -- %(name)s -- [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")
    logger = logging.getLogger()

    load_dotenv()
    uri = os.environ.get("CONNECTION_STRING")
    database = os.environ.get("DATABASE")

    logger.setLevel(level)

    # setup relevant OAuth2 sessions
    client = pymongo.MongoClient(uri)

    try:
        client.admin.command("ping")
        logger.info("successfully connected to database")
    except Exception as e:
        logging.critical(e)
    db = client[database]

    if args.history:
        strava = mdbfit.Strava()
        history = datetime.datetime.strptime(args.history[0], "%Y-%m-%d")
        today = datetime.datetime.now()
        logger.info(f"initiating Strava sync from {history.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")

        inserted_strava_activities = 0
        timespan_delta = datetime.timedelta(days=15)
        after = today - timespan_delta
        before = today

        i = 1
        while before > history:
            logger.debug(f"looking for Strava activities between {after.strftime('%Y-%m-%d')} - {before.strftime('%Y-%m-%d')}")
            activities = strava.get_activities(before.timestamp(), after.timestamp())
            logger.debug(f"found {len(activities)} activities")
            inserted, _ = mdbfit.upload_strava(db, activities)
            inserted_strava_activities += inserted
            before -= timespan_delta
            after -= timespan_delta
            i += 1
            if i % 90 == 0:
                logging.info("pausing for 15 mins to avoid hitting API rate limit")
                time.sleep(15 * 60)

        logger.info(f"inserted {inserted_strava_activities} activities from Strava")


    # insert activities from Strava, recurse backwards until no new activities are found
    if args.strava:
        logger.info("syncing with Strava")
        strava = mdbfit.Strava()

        inserted_strava_activities = 0
        today = datetime.datetime.today()
        timespan_delta = datetime.timedelta(weeks=1)

        before = today
        after = today - timespan_delta
        
        # travel back in time until activities are found
        activities = {}
        while not activities:
            logger.debug(f"looking for Strava activities between {after.strftime('%Y-%m-%d')} - {before.strftime('%Y-%m-%d')}")
            activities = strava.get_activities(before.timestamp(), after.timestamp())
            logger.debug(f"found {len(activities)} activities")
            before -= timespan_delta
            after -= timespan_delta
        
        # recurse back in time until only duplicates are found
        duplicates = 0
        while len(activities) != duplicates:
            inserted, duplicates = mdbfit.upload_strava(db, activities)
            inserted_strava_activities +=  inserted
            before -= timespan_delta
            after -= timespan_delta
        logger.info(f"inserted {inserted_strava_activities} activities from Strava")

    # insert daily step data from Polar
    if args.polar:
        logger.debug("syncing with Polar")
        polar = mdbfit.Polar()
        steps_data = polar.get_steps()
        if steps_data:
            inserted_polar_dates, updated_polar_steps = mdbfit.upload_polar(db, steps_data)
            logger.info(f"inserted {inserted_polar_dates} new dates and updated {updated_polar_steps} dates from Polar")

if __name__ == "__main__":
    main()
