import json
import datetime
import logging
from requests_oauthlib import OAuth2Session
import appdirs
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
STRAVA_REDIRECT_URI = os.environ.get("STRAVA_REDIRECT_URI")
POLAR_CLIENT_SECRET = os.environ.get("POLAR_CLIENT_SECRET")
POLAR_CLIENT_ID = os.environ.get("POLAR_CLIENT_ID")
POLAR_REDIRECT_URI = os.environ.get("POLAR_REDIRECT_URI")

logging.basicConfig(format="%(asctime)s -- %(name)s -- [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)",
                    level=logging.DEBUG)
appname = "mongofitness"
author = "officialankan"


class Strava:
    """Strava OAuth2 session to get activities.

    Attributes
    ----------
    _storage : str
        Path to file in which to write token information used by the OAuth handler. This is set by the `appdirs`
        package.
    _session : OAuth2Session
        OAuth2Session to handle interaction with the Strava API.

    Methods
    -------
    _save_token(token)
        Used by the OAuth2Session object to handle token exchange.
    get_activities(after=None)
        Get activities after a certain epoch timestamp. Defaults to retrieving latest 30 days.

    """

    def __init__(self, level: [logging.INFO, logging.DEBUG] = logging.INFO):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(level)
        self.logger.debug("initializing Strava API object.")
        self._storage = Path(appdirs.user_data_dir(appname, author) + "/strava_token.json")

        if not self._storage.exists():
            self.logger.info("no previous token found, initializing authorization")
            self._session = OAuth2Session(
                client_id=STRAVA_CLIENT_ID,
                redirect_uri=STRAVA_REDIRECT_URI,
                scope="profile:read_all,activity:read_all"
            )
            authorization_url, state = self._session.authorization_url("https://www.strava.com/oauth/authorize")
            self.logger.info(f"please go to {authorization_url} and authorize access.")
            authorization_response = input("enter the full callback URL: ")
            token = self._session.fetch_token(
                "https://www.strava.com/oauth/token",
                authorization_response=authorization_response,
                client_secret=STRAVA_CLIENT_SECRET,
                include_client_id=True
            )
            if not token:
                self.logger.critical("authentication failed.")
        else:
            self.logger.debug("using previous token to initialize OAuth2Session")
            with open(self._storage, mode="r") as fp:
                token = json.loads(fp.read())

        self._session = OAuth2Session(
            client_id=STRAVA_CLIENT_ID,
            redirect_uri=STRAVA_REDIRECT_URI,
            scope="profile:read_all, activity:read_all",
            token=token,
            auto_refresh_url="https://www.strava.com/oauth/token",
            auto_refresh_kwargs={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
            },
            token_updater=self._save_token)
        if self._session.authorized:
            self.logger.info("successfully authenticated Strava.")
        else:
            self.logger.critical("authentication failed")
        self._session.token_updater(self._session.token)

    def _save_token(self, token: dict):
        """Used by the OAuth2Session, this simply saves to a json file.

        Parameters
        ----------
        token

        Returns
        -------

        """
        if not self._storage.parent.exists():
            self.logger.debug(f"creating storage {self._storage.parent}")
            self._storage.parent.mkdir()
        self.logger.debug(f"saving token to {self._storage}")
        with open(self._storage, mode="w") as fp:
            json.dump(token, fp)

    def get_activities(self, before: float, after: float) -> list:
        """Get activities from athlete.

        Parameters
        ----------
        before : float
             An epoch timestamp to use for filtering activities that have taken place before a certain time.

        after : float
            An epoch timestamp to use for filtering activities that have taken place after a certain time.

        Returns
        -------
        list
            List with every activity as a dict.

        """
        before = round(before)
        after = round(after)

        response = self._session.get(f"https://www.strava.com/api/v3/athlete/"
                                     f"activities?before={before}&after={after}")
        response.raise_for_status()

        activities = response.json()
        for activity in activities:
            # format dates to native python
            strava_format = "%Y-%m-%dT%H:%M:%SZ"
            raw = activity["start_date"]
            dt = datetime.datetime.strptime(raw, strava_format)
            raw_local = activity["start_date_local"]
            dt_local = datetime.datetime.strptime(raw_local, strava_format)

            activity["start_date"] = dt
            activity["start_date_local"] = dt_local
        return activities


class Polar:
    def __init__(self, level: [logging.INFO, logging.DEBUG] = logging.INFO):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(level)
        self.logger.debug("initializing Polar API object.")
        self._storage = Path(appdirs.user_data_dir(appname, author) + "/polar_token.json")

        if not self._storage.exists():
            self.logger.info("no previous token found, initializing authorization")
            self._session = OAuth2Session(
                client_id=POLAR_CLIENT_ID,
                redirect_uri=POLAR_REDIRECT_URI,
            )
            authorization_url, state = self._session.authorization_url("https://flow.polar.com/oauth2/authorization")
            self.logger.info(f"please go to {authorization_url} and authorize access.")
            authorization_response = input("enter the full callback URL: ")
            token = self._session.fetch_token(
                "https://polarremote.com/v2/oauth2/token",
                authorization_response=authorization_response,
                client_secret=POLAR_CLIENT_SECRET,
                include_client_id=False
            )
            self.user_id = self._session.token["x_user_id"]
            # register (only required first time)
            register_response = self._session.post("https://www.polaraccesslink.com/v3/users",
                                                   json={"member-id": self.user_id})
            if register_response.status_code == 200:
                self.logger.debug(f"registered user {self.user_id}")
            elif register_response.status_code == 409:
                self.logger.debug("user already registered, but that's fine")
            else:
                self.logger.debug(f"unexpected response when registering user: {register_response.status_code}")

            if not token:
                self.logger.critical("authentication failed.")

        else:
            self.logger.debug("using previous token to initialize OAuth2Session")
            with open(self._storage, mode="r") as fp:
                token = json.loads(fp.read())

        self._session = OAuth2Session(
            client_id=POLAR_CLIENT_ID,
            redirect_uri=POLAR_REDIRECT_URI,
            token=token,
            auto_refresh_url="https://polarremote.com/v2/oauth2/token",
            auto_refresh_kwargs={
                "client_id": POLAR_CLIENT_ID,
                "client_secret": POLAR_CLIENT_SECRET,
            },
            token_updater=self._save_token)

        if self._session.authorized:
            self.logger.info("successfully authenticated Polar.")
        else:
            self.logger.critical("authentication failed")
        self.user_id = self._session.token["x_user_id"]

        self._session.token_updater(self._session.token)

    def _save_token(self, token: dict):
        """Used by the OAuth2Session, this simply saves to a json file.

        Parameters
        ----------
        token

        Returns
        -------

        """
        if not self._storage.parent.exists():
            self.logger.debug(f"creating storage {self._storage.parent}")
            self._storage.parent.mkdir()
        self.logger.debug(f"saving token to {self._storage}")
        with open(self._storage, mode="w") as fp:
            json.dump(token, fp)

    def get_steps(self):
        steps = {}  # {date: {steps: steps, created: created}}
        transaction_response = self._session.post(
            f"https://www.polaraccesslink.com/v3/users/{self.user_id}/activity-transactions"
        )
        if transaction_response.status_code == 201:
            transaction_url = transaction_response.json()["resource-uri"]
            activities = self._session.get(transaction_url).json()
            for url in activities["activity-log"]:
                activity_response = self._session.get(url)
                if activity_response.status_code == 200:
                    activity_dict = activity_response.json()
                    temp_steps = activity_dict["active-steps"]
                    date = datetime.datetime.strptime(activity_dict["date"], "%Y-%m-%d")
                    created = datetime.datetime.strptime(activity_dict["created"], "%Y-%m-%dT%H:%M:%S.%f")

                    # check if greater than last update for this day and if so, update it
                    if (date in steps) and (temp_steps > steps[date]["steps"]):
                        steps[date]["steps"] = temp_steps
                        self.logger.debug(f"updated daily activity data: "
                                          f"{date} | {temp_steps}")
                    elif date in steps:
                        self.logger.debug(
                            f"will not update steps for {date} because {temp_steps} is smaller than current"
                            f" steps for that day ({steps[date]})")
                    else:
                        steps[date] = {"steps": temp_steps, "created": created}
                        self.logger.debug(f"added daily activity data: {date} | steps: {temp_steps} | created: {created}")
            # commit transaction
            self._session.put(transaction_url)
        elif transaction_response.status_code == 204:
            self.logger.debug("status code 204, no new polar data")
        else:
            transaction_response.raise_for_status()
        return steps
