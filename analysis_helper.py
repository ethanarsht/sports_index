import pandas as pd
import numpy as np

def assign_z_score(df):
    '''
    Assign a z-score to each team's performance, based on the mean 
    and standard deviation for their league and year.
    Input:
        df: DataFrame with columns 'league', 'season_year', and 'percentage'
    Returns:
        df: DataFrame with a new column 'z_score'
    '''
    df['z_score'] = df.groupby(
        ['league', 'season_year']
        )['percentage'].transform(lambda x: (x - x.mean()) / x.std())
    return df


def assign_season_order(df):
    '''
    Set the order of seasons across all four leagues
    Input dataframe, returns dataframe with ordering columns
    '''

    df.loc[:, 'season_order'] = np.NaN
    df.loc[df['league'] == 'NHL', 'season_order'] = 0
    df.loc[df['league'] == 'NBA', 'season_order'] = 1
    df.loc[df['league'] == 'MLB', 'season_order'] = 2
    df.loc[df['league'] == 'NFL', 'season_order'] = 3

    df.loc[:, 'chart_position'] = df['season_year'] + df['season_order']*.25
    df = df.sort_values('chart_position').reset_index(drop=True)

    return df

def rolling_string_concat(s_year, s_team, window):
        return [
            ', '.join(
                f"{t} ({y})" 
                for t, y in zip(
                    s_team.iloc[max(0, i - window + 1):i + 1], 
                    s_year.iloc[max(0, i - window + 1):i + 1]
                )
            )
            for i in range(len(s_team))
        ]

def assign_rolling_mean(df, team_selection, rolling_period=4):
    '''
    Assign a rolling mean for the user's selected teams
    and compiles year and teams into a column for tooltip.
    Inputs:
        df: Dataframe with teams and z-scores
        team_selection: list of teams selected by user
        rolling_period: number of seasons to average over, default 4
    Returns:
        df: Dataframe with rolling mean column
    '''
    df['selected'] = df['city_team'].apply(lambda x: 1 if x in team_selection else 0)
    df = df.loc[df['selected'] == 1,:].sort_values(by=['season_year', 'season_order'])
    df['rolling_mean'] = np.NaN
    df['rolling_mean'] = df.groupby(
        'selected')['z_score'].transform(
            lambda x: x.rolling(rolling_period, min_periods=1).mean())

    df['tooltip_teams'] = rolling_string_concat(
            df['season_year'],
            df['name'],
            rolling_period
    )

    return df
  