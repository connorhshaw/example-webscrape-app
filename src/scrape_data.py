import pandas as pd
import requests
import bs4 as bs
import time
import numpy as np
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile
from io import StringIO

def get_games_on_day(day, month, year):
    website_homepage = 'https://www.basketball-reference.com'

    website = f'https://www.basketball-reference.com/boxscores/index.fcgi?month={month}&day={day}&year={year}'

    response = requests.get(url=website)
    if response.status_code == 429:
        print(response.headers["Retry-After"])
    page_data = response.text
    soup = bs.BeautifulSoup(page_data, 'html.parser')

    game_summaries = soup.find_all(class_='game_summary expanded nohover')

    game_list = []

    for game in game_summaries:
        
        game_property_list = []

        table_soup = game.find_all('table')
        table_df = pd.read_html(StringIO(str(table_soup[1])))[0]

        links = str(game.find(class_='links')).split('"')
        box_score_link = website_homepage+links[3]
        play_by_play_link = website_homepage+links[5]
        shot_chart_link = website_homepage+links[7]
        
        a_tags = table_soup[0].find_all('a')
        team_1 = a_tags[0].text
        team_2 = a_tags[2].text
        team_1_abr = a_tags[0]['href'].split('/')[2]
        team_2_abr = a_tags[2]['href'].split('/')[2]
        score_team_1 = table_soup[0].find_all(class_="right")[0].text
        score_team_2 = table_soup[0].find_all(class_="right")[2].text

        game_id = sorted([team_1_abr, team_2_abr])[0]+'-'+sorted([team_1_abr, team_2_abr])[1]+'-'+str(year)+str(month).zfill(2)+str(day).zfill(2)

        game_property_list.append(team_1)
        game_property_list.append(team_2)
        game_property_list.append(score_team_1)
        game_property_list.append(score_team_2)
        game_property_list.append(box_score_link)
        game_property_list.append(play_by_play_link)
        game_property_list.append(shot_chart_link)
        game_property_list.append(game_id)

        game_list.append(game_property_list)

    games_df = pd.DataFrame(game_list)
    games_df.rename({
        0:'team_1',
        1:'team_2',
        2:'score_team_1',
        3:'score_team_2',
        4:'box_score_link',
        5:'play_by_play_link',
        6:'shot_chart_link',
        7:'game_id'
    }, axis=1, inplace=True)

    return games_df

def get_stats_from_game(link, game_id):

    response = requests.get(url=link)
    if response.status_code == 429:
        print(response.headers["Retry-After"])
    page_data = response.text
    soup = bs.BeautifulSoup(page_data, 'html.parser')

    scorebox_soup = soup.find(class_='scorebox_meta').find_all()
    game_date = scorebox_soup[0].get_text()
    game_location = scorebox_soup[1].get_text()

    tables = soup.find_all(class_="stats_table")
    table_list = []

    for table in tables:
        table_name = table.get('id')
        if 'game' in table_name:
            df = pd.read_html(StringIO(str(table)))[0]
            df.columns=df.columns.droplevel(0)
            df['table'] = table_name
            df['date'] = game_date
            df['location'] = game_location
            table_list.append(df)

    df_team_1 = table_list[0].merge(table_list[1], how='left', on='Starters')
    df_team_1.drop([5], inplace=True)
    #df_team_1.drop([len(df_team_1)], inplace=True)
    df_team_1.rename({'Starters':'Player'}, axis='columns', inplace=True)
    df_team_1['Starter'] = False
    df_team_1.loc[0:5, 'Starter'] = True
    #df_team_1['Starter'][0:5] = True

    df_team_2 = table_list[2].merge(table_list[3], how='left', on='Starters')
    df_team_2.drop([5], inplace=True)
    #df_team_2.drop([len(df_team_2)], inplace=True)
    df_team_2.rename({'Starters':'Player'}, axis='columns', inplace=True)
    df_team_2['Starter'] = False
    df_team_2.loc[0:5, 'Starter'] = True

    df_stats = pd.concat([df_team_1, df_team_2])
    df_stats['game_id'] = game_id
    df_stats.reset_index(inplace=True)

    return df_stats

def get_playbyplay_from_game(link, game_id):

    response = requests.get(url=link)
    if response.status_code == 429:
        print(response.headers["Retry-After"])
    page_data = response.text
    soup = bs.BeautifulSoup(page_data, 'html.parser')

    table = pd.read_html(StringIO(str(soup.find(class_="stats_table"))))[0]
    table.columns=table.columns.droplevel(0)
    left_team = table.columns[1]
    right_team = table.columns[5]
    table.rename(columns={
        table.columns[0]: "time",
        table.columns[1]: "team_1_description",
        table.columns[2]: "team_1_points",
        table.columns[3]: "score",
        table.columns[4]: "team_2_points",
        table.columns[5]: "team_2_description"
        }, inplace = True)
    table['team_1'] = np.where(table['team_1_description'].isna() == False,left_team, '')
    table['team_2'] = np.where(table['team_2_description'].isna() == False,right_team, '')
    table['team'] = table['team_1']+table['team_2']
    table.drop('team_1', axis=1, inplace=True)
    table.drop('team_2', axis=1, inplace=True)
    table['description'] = table['team_1_description'].astype(str).replace('nan', '')+table['team_2_description'].astype(str).replace('nan', '')
    table.drop('team_1_description', axis=1, inplace=True)
    table.drop('team_2_description', axis=1, inplace=True)

    table['quarter'] = table['time'].str.contains('Q').cumsum()+1
    
    table['game_id'] = game_id
    return table

def get_shots_from_game(link, game_key):

    response = requests.get(url=link)
    if response.status_code == 429:
        print(response.headers["Retry-After"])
    page_data = response.text
    soup = bs.BeautifulSoup(page_data, 'html.parser')
    shot_areas = soup.find_all(class_="shot-area")

    shots = shot_areas[0].find_all('div')
    shots = shots+shot_areas[1].find_all('div')

    shot_list = []

    for shot in shots:
        temp_list = []
        temp_list.append(shot.get_text().replace('●', 'make').replace('×', 'miss'))

        coord_list = shot['style'].replace(':',';').split(";", 4)
        temp_list.append(coord_list[1])
        temp_list.append(coord_list[3])

        tip_list = shot['tip'].replace('<br>', ', ').split(', ')
        for item in tip_list:
            temp_list.append(item)

        description_list = tip_list[2].split(' ')
        points = description_list[len(description_list)-4].split('-')[0]
        distance = description_list[len(description_list)-2]
        player = tip_list[2].replace('missed', 'made').split('made')[0].strip()

        temp_list.append(player)
        temp_list.append(points)
        temp_list.append(distance)

        shot_list.append(temp_list)
    
    shot_df = pd.DataFrame(shot_list)
    shot_df.rename({
        0:'make_or_miss',
        1:'dist_from_top',
        2:'dist_from_left',
        3:'quarter',
        4:'time_remaining_in_quarter',
        5:'text',
        6:'points_update',
        7:'player',
        8:'points_scored',
        9:'shot_distance_ft'
    }, axis=1, inplace=True)
    shot_df['dist_from_top'] = shot_df['dist_from_top'].str.replace('px', '')
    shot_df['dist_from_left'] = shot_df['dist_from_left'].str.replace('px', '')
    shot_df['game_key'] = game_key
    
    return shot_df

#def get_data_from_date(day, month, year):
#
#    game_data = get_games_on_day(day, month, year)
#
#    shots_data = []
#
#   for i in range(len(game_data)):
#        time.sleep(2)
#        #print(game_data['shot_chart_link'][i])
#        shots_from_game = get_shots_from_game(game_data['shot_chart_link'][i], 'test')
#        shots_data.append(shots_from_game)

#    print(game_data)
#    print(shots_data)
#    shots_data_df = pd.concat(shots_data)
#    print(shots_data_df)

def get_games_between_dates(date_1, date_2):

    if date_2 < date_1:
        return "n/a"
    
    date_list = pd.date_range(start=date_1,end=date_2).to_list()
    game_list = []

    for date in date_list:
        time.sleep(4)
        game_list.append(get_games_on_day(date.day, date.month, date.year))

    return pd.concat(game_list)

def get_shots_from_games(links):

    shot_list = []

    for i in range(0, len(links)):
        time.sleep(4)
        shot_list.append(get_shots_from_game(links.iloc[i]['shot_chart_link'], links.iloc[i]['game_id']))

    return pd.concat(shot_list)

def get_stats_from_games(links):
    stat_list = []

    for i in range(0, len(links)):
        time.sleep(4)
        stat_list.append(get_stats_from_game(links.iloc[i]['box_score_link'], links.iloc[i]['game_id']))

    return pd.concat(stat_list)

def get_plays_from_games(links):
    stat_list = []

    for i in range(0, len(links)):
        time.sleep(4)
        stat_list.append(get_playbyplay_from_game(links.iloc[i]['play_by_play_link'], links.iloc[i]['game_id']))

    return pd.concat(stat_list) 

def get_all_data_between_dates(date_1, date_2):

    if date_2 < date_1:
        return "n/a"
    
    game_data = get_games_between_dates(date_1, date_2)

    shot_data = get_shots_from_games(game_data[['shot_chart_link', 'game_id']])
    stat_data = get_stats_from_games(game_data[['box_score_link', 'game_id']])
    play_data = get_plays_from_games(game_data[['play_by_play_link', 'game_id']])

    return_dict = {
        'games':game_data,
        'shots':shot_data,
        'stats':stat_data,
        'plays':play_data
    }

    return return_dict

def get_all_data_on_date(date):
    
    game_data = get_games_between_dates(date, date)

    shot_data = get_shots_from_games(game_data[['shot_chart_link', 'game_id']])
    stat_data = get_stats_from_games(game_data[['box_score_link', 'game_id']])
    play_data = get_plays_from_games(game_data[['play_by_play_link', 'game_id']])

    return_dict = {
        'games':game_data,
        'shots':shot_data,
        'stats':stat_data,
        'plays':play_data
    }

    return return_dict

