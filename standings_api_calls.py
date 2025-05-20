import time
import re
import os

from nba_api.stats.endpoints import LeagueStandings
import statsapi

import requests
import spacy

import pandas as pd

nlp = spacy.load("en_core_web_sm")

city_grouping = {
    'Boston': ['New England'],
    'South Florida': ['Miami', 'Florida'],
    'Bay Area': ['San Francisco', 'Oakland', 'San Jose', 'Golden State'],
    'Los Angeles': ['Anaheim', 'California', 'LA'],
    'Dallas': ['Texas'],
    'Denver': ['Colorado'],
    'New York': ['NY Rangers', 'NY Islanders'],
    'Washington': ['Capital'],
    'Kansas City': ['Kansas City-Omaha'],
    'New Orleans': ['New Orleans/Oklahoma City'],
    'Montreal': ['Montréal'],
    'Phoenix': ['Arizona'],
    'Carolina': ['Charlotte'],
    'Indiana': ['Indianapolis'],
    'Las Vegas': ['Vegas']
}

inverted_grouping = {}
for key, values in city_grouping.items():
    for value in values:
        inverted_grouping[value] = key

NHL_URL = "https://api-web.nhle.com/v1/standings-season"


def nhl_season_constructor(start, stop):
    """
    Construct NHL seasons with date for standing API calls.
    Dates are used to get request NHL standings API directly.
    """
    season_info = requests.get(NHL_URL).json()
    season_dict = {}

    for season in season_info['seasons']:
        season_year = int(str(season['id'])[-4:])
        season_end_date = season['standingsEnd']

        if season_year >= start and season_year < stop:
            season_dict[season_year] = season_end_date
        
    return season_dict


def get_nhl_standings(season, nhl_dict):
    """
    Get request NHL API for standings for an individual season.

    Inputs:
        season: int, season year
        nhl_dict: dict, dictionary of NHL seasons with dates
    
    Returns:
        DataFrame with that season's standings.
    """
    season_date_key = nhl_dict[season]

    standings_url_prefix = 'https://api-web.nhle.com/v1/standings/'
    year_json = requests.get(
        f"{standings_url_prefix}{season_date_key}",
        timeout=10
    ).json()

    standings = year_json['standings']

    city_list = []
    name_list = []
    percentage_list = []
    for t in standings:
        city = t['placeName']
        name = t['teamCommonName']
        percentage = t['pointPctg']

        city_list.append(city)
        name_list.append(name)
        percentage_list.append(percentage)

    df_standings_year = pd.DataFrame({
        'city': city_list,
        'name': name_list,
        'percentage': percentage_list
    })

    df_standings_year.loc[:, 'city'] = df_standings_year['city'].apply(lambda x: x['default'])
    df_standings_year.loc[:, 'name'] = df_standings_year['name'].apply(lambda x: x['default'])

    df_standings_year.loc[:, 'season_year'] = season
    df_standings_year.loc[:, 'season'] = str(str(season-1)+str(season))

    return df_standings_year

 
def nhl_combine(start, stop):
    """
    Combine NHL standings for multiple seasons

    Inputs: 
        start: int, start year
        stop: int, stop year
    
    Returns:
        DataFrame with all NHL standings in specified years.
    """
    nhl_dict = nhl_season_constructor(start, stop)

    df_all_standings = pd.DataFrame()

    for s in range(start, stop, 1):
        if s != 2005:
            df_all_standings = pd.concat([df_all_standings, get_nhl_standings(s, nhl_dict=nhl_dict)])
    df_all_standings = df_all_standings.reset_index(drop=True)
    df_all_standings.loc[:, 'league'] = 'NHL'

    return df_all_standings

 
def nba_season_constructor(start, stop):
    """
    Construct NBA season strings compatible with API calls

    Inputs:
    start: int, start year
    stop: int, stop year

    Returns a list of strings.
    """
    nba_season_strings = []
    for s in range(start,stop,1):
        first_year = str(s-1)
        current_year = str(s)[-2:]
        season = first_year + '-' + current_year
        nba_season_strings.append(season)
    return nba_season_strings

 
def get_nba_standings(season):
    """
    Get NBA standings for a given season.

    Input:
    season: str, season string

    Returns a DataFrame with that season's standings.
    """
    time.sleep(1)
    standings_resp = LeagueStandings(season=season)
    df_standings = standings_resp.get_data_frames()[0]
    df_standings = df_standings.loc[:, ['TeamCity', 'TeamName', 'WinPCT']]
    df_standings = df_standings.rename(columns={'TeamCity': 'city',
                                        'TeamName': 'name',
                                        'WinPCT': 'percentage'})
    
    season_year = int(season[-2:])
    if season_year <= 25:
        if season_year < 10:    
            season_end = "200"+str(season_year)
        else:
            season_end = "20"+str(season_year)
    else:
        season_end = "19"+str(season_year)
    df_standings.loc[:, 'season'] = season
    df_standings.loc[:, 'season_year'] = season_end
    
    return df_standings

 
def nba_combine(start, stop):
    """
    Combine NBA standings for multiple seasons
    
    Inputs:
    start: int, start year
    stop: int, stop year
    
    Returns a DataFrame with all NBA standings in specified years.
    """
    seasons = nba_season_constructor(start, stop)
   
    df_all_standings = pd.DataFrame()
    for s in seasons:
        df_all_standings = pd.concat([df_all_standings, get_nba_standings(season=s)])

    df_all_standings.loc[:,'league'] = 'NBA'
    return df_all_standings

mlb_localities = [
    "Arizona",
    "Atlanta",
    "Baltimore",
    "Boston",
    "Brooklyn",
    "California",
    "Chicago",
    "Cincinnati",
    "Cleveland",
    "Colorado",
    "Detroit",
    "Florida",
    "Houston",
    "Kansas City",
    "Los Angeles",
    "Miami",
    "Milwaukee",
    "Minnesota",
    "Montreal",
    "New York",
    "Oakland",
    "Philadelphia",
    "Pittsburgh",
    "San Diego",
    "San Francisco",
    "Seattle",
    "St. Louis",
    "Tampa Bay",
    "Texas",
    "Toronto",
    "Washington",
    "Anaheim"
]

def extract_city(text):
    """
    Extract city from team name
    Input: text, str of combined team name (city + name)
    Returns: str, city name
    """
    for pattern in mlb_localities:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None


def get_mlb_standings(s):
    """
    Get MLB standings for a given season

    Input: s, int, season year
    Returns: DataFrame with that season's standings
    """
    data = statsapi.standings_data(season=s)

    team_names = []
    percentages = []
    for div in data.keys():
        div_standings = data[div]
        teams = div_standings['teams']
        for team in teams:
            team_names.append(team['name'])
            percentages.append(team['w'] / (team['w'] + team['l']))

    df = pd.DataFrame(
        {
            'team_name': team_names,
            'percentage': percentages
        }
    )
    df.loc[:, 'season'] = s
    df.loc[:, 'season_year'] = str(s)

    return df


def mlb_combine(start, stop=None):
    """
    Combine MLB standings for multiple seasons
    
    Inputs:
    start: int, start year
    stop: int, stop year
    
    Returns a DataFrame with all MLB standings in specified years.
    """
    if not stop:
        stop = start+1
    df_all_mlb = pd.DataFrame()

    for s in range(start, stop, 1):
        df_season = get_mlb_standings(s)
        df_all_mlb = pd.concat([df_all_mlb, df_season])

    df_final = df_all_mlb.rename(columns={'team_name':'team'})[['team', 'percentage', 'season', 'season_year']]
    df_final.loc[:, 'city'] = df_final['team'].apply(extract_city).str.strip()
    df_final.loc[:, 'name'] = df_final.apply(lambda row: row['team'].replace(row['city'], ''), axis=1).str.strip()
    df_final.loc[:, 'league'] = 'MLB'
    df_final = df_final.drop('team', axis=1)
    return df_final


def get_nfl_standings(season):
    """
    Get NFL standings for a given season
    
        Input: season, int, season year
        Returns: DataFrame with that season's standings
    """

    url = f"https://site.api.espn.com/apis/v2/sports/football/nfl/standings?season={season}"
    response = requests.get(url, timeout=10)
    data = response.json()

    names = []
    locations = []
    percents = []

    if 'standings' not in data.keys():
        entries = []
        for c in [0,1]:
            entries.extend(data['children'][c]['standings']['entries'])
    else:
        entries = data['standings']['entries']
    for e in entries:
        team_info = e['team']
        if 'name' in team_info.keys():
            name = team_info['name']
        else:
            name = 'Football Team'
        location = team_info['location']

        stats_info = e['stats']
        for l in stats_info:
            if l['name'] == 'winPercent':
                percentage = l['value']

        names.append(name)
        locations.append(location)
        percents.append(percentage)


    df_season = pd.DataFrame(
        {
            'name': names,
            'city': locations,
            'percentage': percents
        }
    )

    df_season.loc[:, 'season'] = season
    df_season.loc[:, 'season_year'] = str(season)
    return df_season


def nfl_combine(start, stop=None):
    """
    Combine NFL standings for multiple seasons
    """
    if stop is None:
        stop = start
    df_all_nfl = pd.DataFrame()
    for y in range(start, stop, 1):
        df_season = get_nfl_standings(y)
        df_all_nfl = pd.concat([df_all_nfl, df_season])
    
    df_all_nfl.loc[:, 'league'] = 'NFL'
    return df_all_nfl


def construct_dataset(start, stop, league='all'):
    """
    Construct dataset for all leagues

    Inputs:
    start: int, start year
    stop: int, stop year
    league: str, league(s) to include, default to 'all' for all leagues

    Returns:
    DataFrame with all standings in specified years.
    """
    df = pd.DataFrame()

    if league in ['all', 'NHL']:
        print('NHL')
        df_nhl = nhl_combine(start, stop)
        df = pd.concat([df, df_nhl])

    if league in ['all', 'MLB']:
        print('MLB')
        df_mlb = mlb_combine(start, stop)
        df = pd.concat([df, df_mlb])

    if league in ['all', 'NBA']:
        print('NBA')
        df_nba = nba_combine(start, stop)
        df = pd.concat([df, df_nba])

    if league in ['all', 'NFL']:
        print('NFL')
        df_nfl = nfl_combine(start, stop)
        df = pd.concat([df, df_nfl])

    df['city_group'] = df.loc[:, 'city'].replace(inverted_grouping)
    # Move Golden Seals to Bay Area
    df.loc[df['name'] == 'Golden Seals', 'city_group'] = 'Bay Area'
    df.loc[:, 'season_year'] = df['season_year'].astype(int)

    return df


def main(start=1969, stop=2025, league='all', csv=True, cached=False):
    """
    Main function to construct dataset

    start: int, start year, default to 1969
    stop: int, stop year, default to 2025
    league: str, league(s) to include, default to 'all' for all leagues
    csv: bool, save to csv and returns dataframe if True, otherwise only returns dataframe
    cached: bool, use existing csv if true, default to False

    Returns:
    DataFrame with all standings in specified years.
    """

    if cached:
        if 'all_standings.csv' in os.listdir('data'):
            df = pd.read_csv('data/all_standings.csv')
            return df

    df = construct_dataset(start=start, stop=stop, league=league)
    if csv:
        df.to_csv('data/all_standings.csv', index=False)
        return df
    else:
        return df

if __name__ == "__main__":
    main()
