# Sports Success Index
A project to estimate the sports success of an individual city at a given time between 1969 and present.

## Products
Flask app here: https://sports-index.onrender.com/
Blog post here: https://ethanarsht.github.io/sports_index/

## How to use
Assuming you want to use the standings data, the best approach is to clone the repository and run `standings_api_call.py` from the command line i.e. `python3 standings_api_call.py`. This will produce a csv with all of the standings data from 1969-2024. Users looking for more granular information can use that same script as a module and take advantage of the utilities for standings for a particular season.

## Contributing
The most straightforward way to contribute is by adding additional years and/or leagues (EPL, WNBA, etc). Contributing a league should follow the basic nomenclature used in `standings_api_call.py`. This has a minimum of two functions: `get_<league_abbreviation>_season`, which returns a Pandas dataframe for one season's results across the entire league, and `<league_abbreviation>_combine` which applies the `get_<league_abbreviation>_season` for the desired years. This approach seems to offer easy debugging (it's easy to see which league and year is causing problems), and keeps the approach consistent across all years.
