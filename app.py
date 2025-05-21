import base64
import io
import random
import numpy as np
import matplotlib.pyplot as plt

from dash import Dash, html, dcc, callback, Input, Output
import dash_daq as daq
import dash_bootstrap_components as dbc
import plotly.express as px

from utils import assign_z_score, assign_season_order, assign_rolling_mean, plot_city_year
import standings_api_calls

external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    {
        'href': 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
        'rel': 'stylesheet',
        'integrity': 'sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO',
        'crossorigin': 'anonymous'
    }
]

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

df = standings_api_calls.main(league='all', csv=False, cached=True)
df = assign_z_score(df)
df = assign_season_order(df)
df['city_team'] = df['city'] + ' ' + df['name']
grouped_standings = df.groupby(['season_year', 'city_group'])['z_score'].agg(['sum', 'mean', 'count']).reset_index()
df_checklists = df.drop_duplicates(subset=['city_team'])

# Precompute a valid city-year pair
valid_city_years = df.groupby(['city_group', 'season_year']).size().reset_index(name='count')
valid_city_years = valid_city_years[valid_city_years['count'] > 0]
random_row = valid_city_years.sample(1).iloc[0]
random_city = random_row['city_group']
random_year = random_row['season_year']

app.layout = dbc.Container([
    html.H1('A History of Sports Happiness'),
    dcc.Store(id='current-tab', data='rolling'),
    dcc.Tabs(id='tabset', value='rolling', children=[
        dcc.Tab(label='City Charts', value='charts'),
        dcc.Tab(label='Rolling Averages', value='rolling')
    ]),
    html.Div(id='rolling-tab-content', style={'display': 'block'}, children=[]),
    html.Div(id='charts-tab-content', style={'display': 'none'}, children=[])
])

# Callbacks to manage tab switching
@callback(
    Output('current-tab', 'data'),
    Input('tabset', 'value')
)
def store_tab(tab):
    return tab

@callback(
    Output('rolling-tab-content', 'style'),
    Output('charts-tab-content', 'style'),
    Input('current-tab', 'data')
)
def toggle_tabs(tab):
    return (
        {'display': 'block'}, {'display': 'none'}
    ) if tab == 'rolling' else (
        {'display': 'none'}, {'display': 'block'}
    )

# Rolling tab content (static)
app.layout.children[3].children = html.Div([
    html.Div([
        dcc.Graph(id='happiness-graph', style={'width': '100%'})
    ], style={'marginBottom': '30px'}),

    html.Div([
        daq.NumericInput(
            id='rolling-period', min=1, max=10, value=4,
            label="Rolling Period", labelPosition='top'
        )
    ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '30px'}),

    html.Div([
        html.Div([
            html.Label('City'),
            dcc.Checklist(id='city-selection', options=[
                {'label': city, 'value': city} for city in np.sort(df_checklists['city_group'].unique())
            ], value=['Atlanta'])
        ], style={'flex': '1', 'minWidth': '200px'}),

        html.Div([
            html.Label('MLB'),
            dcc.Checklist(id='mlb-selection', options=[
                {'label': team, 'value': team} for team in sorted([
                    city_team for city_team, league in zip(df_checklists['city_team'], df_checklists['league']) if league == 'MLB'
                ])
            ], value=[])
        ], style={'flex': '1', 'minWidth': '200px'}),

        html.Div([
            html.Label('NHL'),
            dcc.Checklist(id='nhl-selection', options=[
                {'label': team, 'value': team} for team in sorted([
                    city_team for city_team, league in zip(df_checklists['city_team'], df_checklists['league']) if league == 'NHL'
                ])
            ], value=[])
        ], style={'flex': '1', 'minWidth': '200px'}),

        html.Div([
            html.Label('NBA'),
            dcc.Checklist(id='nba-selection', options=[
                {'label': team, 'value': team} for team in sorted([
                    city_team for city_team, league in zip(df_checklists['city_team'], df_checklists['league']) if league == 'NBA'
                ])
            ], value=[])
        ], style={'flex': '1', 'minWidth': '200px'}),

        html.Div([
            html.Label('NFL'),
            dcc.Checklist(id='nfl-selection', options=[
                {'label': team, 'value': team} for team in sorted([
                    city_team for city_team, league in zip(df_checklists['city_team'], df_checklists['league']) if league == 'NFL'
                ])
            ], value=[])
        ], style={'flex': '1', 'minWidth': '200px'})
    ], style={
        'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'justifyContent': 'center'
    })
])

# Charts tab content (static)
app.layout.children[4].children = html.Div([
    html.Div([
        html.Div([
            html.Label('City'),
            dcc.Dropdown(id='city-chart', options=[
                {'label': city, 'value': city} for city in np.sort(df_checklists['city_group'].unique())
            ], value=random_city, style={'width': '200px'})
        ], style={'margin': '0 10px'}),

        html.Div([
            html.Label('Year'),
            dcc.Dropdown(id='year-chart', options=[
                {'label': year, 'value': year} for year in np.sort(df['season_year'].unique())
            ], value=random_year, style={'width': '150px'})
        ], style={'margin': '0 10px'})
    ], style={
        'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '20px'
    }),

    html.Div([
        html.Img(id='city-graph', style={'maxWidth': '100%', 'height': 'auto'})
    ], style={'display': 'flex', 'justifyContent': 'center'})
])

@callback(
    Output('city-graph', 'src'), 
    Input('city-chart', 'value'),
    Input('year-chart', 'value')
)

def update_city_graph(city, year):
    fig = plot_city_year(city, year, df, grouped_standings)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight') 
    buf.seek(0)
    data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return f'data:image/png;base64,{data}'

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
    df_chart = assign_rolling_mean(df, team_selection, rolling_value).rename(columns={'tooltip_teams': 'Teams in Average'})
    df_chart = df_chart[df_chart['selected'] == 1]
    fig = px.line(df_chart, x='chart_position', y='rolling_mean',
                  labels={'season_year': 'Year', 'rolling_mean': 'Rolling Mean Z-Score'},
                  hover_data={'Teams in Average':True,
                              'chart_position':False},
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