from dash import Dash, html, dcc, callback, Input, Output
import dash_daq as daq
import dash_bootstrap_components as dbc

import plotly.express as px
from analysis_helper import assign_z_score, assign_season_order, assign_rolling_mean
import standings_api_calls
import numpy as np

app = Dash(
    external_stylesheets=[dbc.themes.SOLAR]
)

df = standings_api_calls.main(
    league='all',
    csv=False,
    cached=True
)
df = assign_z_score(df)
df = assign_season_order(df)
df['city_team'] = df['city'] + ' ' + df['name']

df_checklists = df.drop_duplicates(subset=['city_team'])

app.layout = dbc.Container([
    html.H1('A History of Sports Happiness'),
    # Create a graph with the rolling period control directly to its right
    html.Div([
        html.Div([
            dcc.Graph(id='happiness-graph')
        ],  style={'width': '90%', 'display': 'inline-block'}),

        html.Div([
            daq.NumericInput(id='rolling-period',
                    min=1,
                    max=10,
                    value=4,
                    label="Rolling Period",
                    labelPosition='top'
            )
    ], style={'verticalAlign': 'top', 'width': '10%', 'display': 'inline-block'}),
    ]),
    html.Div([
        html.Div([
            html.Label('City'),
            dcc.Checklist(id='city-selection',
                    options=[
                        {'label': city, 'value': city} for city in np.sort(df_checklists['city_group'].unique())
                        ],
                        value=[]
                    )],
                    style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}
        ),
        html.Div([
            html.Label('MLB'),
            dcc.Checklist(id='mlb-selection',
                    options=[city_team for city_team, league in zip(
                        df_checklists['city_team'], df_checklists['league']
                        ) if league == 'MLB'],
                        value=[]
                    )],
                    style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}
        ),
        html.Div([
            html.Label('NHL'),
            dcc.Checklist(id='nhl-selection',
                    options=[city_team for city_team, league in zip(
                        df_checklists['city_team'], df_checklists['league']
                        ) if league == 'NHL'],
                        value=[]
                    )],
                    style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}
        ),
        html.Div([
            html.Label('NBA'),
            dcc.Checklist(id='nba-selection',
                    options=[city_team for city_team, league in zip(
                        df_checklists['city_team'], df_checklists['league']
                        ) if league == 'NBA'],
                        value=[]
                    )],
                    style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}
        ),
        html.Div([
            html.Label('NFL'),
            dcc.Checklist(id='nfl-selection',
                    options=[city_team for city_team, league in zip(
                        df_checklists['city_team'], df_checklists['league']
                        ) if league == 'NFL'],
                        value=[]
                    )],
                    style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}
        )
    ]
    )
])

@callback(
    Output('happiness-graph', 'figure'),
    Input('mlb-selection', 'value'),
    Input('nhl-selection', 'value'),
    Input('nba-selection', 'value'),
    Input('nfl-selection', 'value'),
    Input('rolling-period', 'value')
)
def update_graph(mlb_selection,
                 nhl_selection,
                 nba_selection,
                 nfl_selection,
                 rolling_value):
    team_selection = []
    for selection in [mlb_selection, nhl_selection, nba_selection, nfl_selection]:
        if selection:
            team_selection.extend(selection)
    df_chart = assign_rolling_mean(df, team_selection, rolling_value)
    df_chart = df_chart[df_chart['selected'] == 1]
    fig = px.line(df_chart, x='chart_position', y='rolling_mean',
                  labels={'chart_position': 'Season Year'},
                  hover_data=['tooltip_teams'],
                  title='Rolling Mean Z-Score of Selected Teams')
    return fig

@callback(
    Output('mlb-selection', 'value'),
    Output('nhl-selection', 'value'),
    Output('nba-selection', 'value'),
    Output('nfl-selection', 'value'),
    Input('city-selection', 'value')
)
def update_selection(city_selection):
    '''
    Select all teams representing the selected cities.
    Input:
        city_selection: list of selected cities
    Returns:
        Selections for each league
    '''
    mlb_selection = df_checklists.loc[
        df_checklists['city_group'].isin(city_selection) &
              (df_checklists['league'] == 'MLB'), 'city_team'].tolist()
    nhl_selection = df_checklists.loc[
        df_checklists[
            'city_group'].isin(city_selection) &
              (df_checklists['league'] == 'NHL'), 'city_team'].tolist()
    nba_selection = df_checklists.loc[
        df_checklists[
            'city_group'].isin(city_selection) &
              (df_checklists['league'] == 'NBA'), 'city_team'].tolist()
    nfl_selection = df_checklists.loc[
        df_checklists[
            'city_group'].isin(city_selection) &
              (df_checklists['league'] == 'NFL'), 'city_team'].tolist()
    return mlb_selection, nhl_selection, nba_selection, nfl_selection

if __name__ == '__main__':
    app.run(debug=True)