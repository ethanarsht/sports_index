import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import json

colors = json.load(open('data/teams.json'))

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

def create_main_plot(fig, ax, city, year, df):
    df_city_year = df[
        (df['city_group'] == city) &
        (df['season_year'] == year)
    ]

    sns.set_style("dark")
    sns.histplot(df, x='sum', ax=ax, alpha=0.5, bins=30, color='blue')
    if not df_city_year.empty:
        ax.axvline(df_city_year['sum'].values[0], color='red', linestyle='--')
    ax.set_title(f'{city} in {year} vs All Other Cities and Years')
    ax.set_xlabel('Sum of Z-Scores')
    ax.set_ylabel('Number of Cities')
    ax.legend([f'{city} in {year}', 'All Cities'])

    ax.set_xlim(-7,7)  

def get_colors(team, league):

    team_colors = [c for c in colors if team in c['name'] and c['league'] == league.lower()]
    if len(team_colors) == 1 and team_colors[0]['league'] != 'nba':
        if len(team_colors[0]['colors']['hex']) > 1:
            team_color = '#' + team_colors[0]['colors']['hex'][0]
            gapcolor = '#' + team_colors[0]['colors']['hex'][1]
        else:
            team_color = '#' + team_colors[0]['colors']['hex'][0]
            gapcolor = 'gray'
    elif len(team_colors) == 1 and team_colors[0]['league'] == 'nba':
        if len(team_colors[0]['colors']['rgb']) > 1:
            team_color = [c for c in team_colors[0]['colors']['rgb'][0].split(' ')]
            team_color = tuple([int(c)/255 for c in team_color])
            gapcolor = [c for c in team_colors[0]['colors']['rgb'][1].split(' ')]
            gapcolor = tuple([int(c)/255 for c in gapcolor])
        else:
            team_color = [c for c in team_colors[0]['colors']['rgb'][0].split(' ')]
            team_color = tuple([int(c)/255 for c in team_color])
            gapcolor = 'gray'
    else:
        team_color = 'gray'   
        gapcolor = 'gray' 
    return team_color, gapcolor

def determine_limits(df, year):

    df_year = df[df['season_year'] == year]
    min_val = df_year['z_score'].min()
    max_val = df_year['z_score'].max()
    print(df_year)

    setter = max(abs(min_val), abs(max_val))
    if setter < 0:
        setter = setter * -1
    return setter

def create_subplots(fig, ax, grid_spec, year, df, standings):
    xlim_setter = determine_limits(standings, year)
     
    for ix, (team, league) in enumerate(zip(df['name'], df['league'])):
        row = (ix // 2) + 1
        col = ix % 2
        ax = fig.add_subplot(grid_spec[row, col])
        df_kde = standings[
            (standings['season_year'] == year) &
            (standings['league'] == league)
        ]

        team_color, gapcolor = get_colors(team, league)

        sns.set_style("dark")

        sns.histplot(df_kde, x='z_score', ax=ax, label=f'{league} {year}', alpha=0.25, color='blue', kde=True)

        ax.axvline(df.iloc[ix]['z_score'], color=team_color, gapcolor=gapcolor, linestyle='--', label=team)
        ax.set_title(f'{team} {year}')
        ax.set_xlabel('Team Z-Score')
        ax.set_ylabel('Teams')
        ax.legend()
        ax.label_outer()

        ax.set_xlim(-xlim_setter-xlim_setter*.1, xlim_setter+xlim_setter*.1)

def plot_city_year(city, year, df, grouped_df):
    df_teams = df[
        (df['city_group'] == city) &
        (df['season_year'] == year)
    ]
    
    num_teams = len(df_teams)
    n_rows = (num_teams + 1) // 2  # 2 plots per row

    # Create a grid with space for a large top plot + team plots below

    fig = plt.figure(figsize=(11, 4 + n_rows * 3))
    gs = gridspec.GridSpec(n_rows + 1, 2, height_ratios=[1.2] + [1]*n_rows)

    ax = fig.add_subplot(gs[0, :])
    # Top row: full-width city-level KDE plot
    create_main_plot(fig=fig, ax=ax, city=city, year=year, df=grouped_df)

    # Team-level KDEs

    create_subplots(
        fig=fig, ax=ax, grid_spec=gs, year=year, df=df_teams, standings=df
    )

    fig.suptitle(f'{city} {year}: Normalized Results Across Teams', fontsize=16, fontweight='bold')
    return fig