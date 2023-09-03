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
4. Run `main.py -h` with your poetry environment to see available run arguments.

## Usage

```shell
python main.py [-h] [--strava] [--polar] [--history HISTORY] [--verbose]
```

## Contributing

## License

