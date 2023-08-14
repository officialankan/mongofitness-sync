# mongofitness

upload activities from Strava and daily steps from Polar to a MongoDB database.

## Installation

1. Clone this repository.
2. Install with `poetry install`
3. Create a `.env` file with the following content:

    ```
    STRAVA_CLIENT_ID=102436
    STRAVA_CLIENT_SECRET=54bc839e1304ac307f29fb8a6ed72a9c593f543b
    STRAVA_REDIRECT_URI=https://localhost/strava_exchange_token
    POLAR_CLIENT_ID=35681e4c-26d0-443f-8aa1-5065b57cc0f4
    POLAR_CLIENT_SECRET=ae56b587-e0fc-408d-8733-1cccdef9fbd1
    POLAR_REDIRECT_URI=https://localhost/polar_exchange_token
    CONNECTION_STRING=<mongodb connection string>
    DATABASE=<database name>
    ```
    
    last two variables need to be set by you!
4. Run `main.py` with your poetry environment. When running for the first time, pay attention to the output as it will provide a URL for authorization from both Strava and Polar. The first run may be long due if you have a lot of Strava activities.

`main.py` assumes there is not a gap in Strava activities longer than 10 weeks. This should be modified to be more intelligent, but in the meantime you can also just change the `timespan_delta` variable in `main.py`.
   

## Usage

```shell
python main.py
```

## Contributing

## License

