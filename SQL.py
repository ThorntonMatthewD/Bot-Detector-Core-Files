

from Config import db
from sqlalchemy import text
from collections import namedtuple
import time
import random
import string


def execute_sql(sql, param=None, debug=False, has_return=True):
    # example
    sql = text(sql)
    if debug:
        print(f'SQL : {sql}')
        print(f'Param: {param}')

    if has_return:
        rows = db.session.execute(sql, param)
        db.session.close()
        Record = namedtuple('Record', rows.keys())
        records = [Record(*r) for r in rows.fetchall()]

        if debug:
            print(f'keys: {rows.keys()}')
        return records
    else:
        db.session.execute(sql, param)
        db.session.commit()


def get_player(player_name):
    sql_player_id = 'select * from Players where name = :player_name;'
    param = {
        'player_name': player_name
    }
    
    # returns a list of players
    player = execute_sql(sql_player_id, param=param,
                            debug=False, has_return=True)
    
    if len(player) == 0:
        player_id = None
    else:
        player_id = player[0] 
        
    return player_id


def insert_player(player_name):
    sql_insert = "insert ignore into Players (name) values(:player_name);"

    param = {
        'player_name': player_name
    }
    execute_sql(sql_insert, param=param, debug=False, has_return=False)
    player = get_player(player_name)
    return player


def list_to_string(l):
    string_list = ', '.join(str(item) for item in l)
    return string_list


def insert_highscore(player_id, skills, minigames):
    columns = list_to_string(
        ['player_id'] + list(skills.keys()) + list(minigames.keys()))
    values = list_to_string(
        [player_id] + list(skills.values()) + list(minigames.values()))

    # f string is not so secure but we control the skills & minigames dict
    sql_insert = f"insert ignore into playerHiscoreData ({columns}) values ({values});"
    execute_sql(sql_insert, param=None, debug=False, has_return=False)


def insert_report(data):
    param = {
        'reportedID': data['reported'],
        'reportingID': data['reporter'],
        'region_id': data['region_id'],
        'x_coord': data['x'],
        'y_coord': data['y'],
        'z_coord': data['z'],
        'timestamp': data['ts'],
        'manual_detect': data['manual_detect']
    }
    # list of column values
    columns = list_to_string(list(param.keys()))
    values = list_to_string([f':{column}' for column in list(param.keys())])

    sql_insert = f'insert ignore into Reports ({columns}) values ({values});'
    execute_sql(sql_insert, param=param, debug=False, has_return=False)

def update_player(player_id, possible_ban=0, confirmed_ban=0, confirmed_player=0, label_id=0, debug=False):
    sql_update = 'update Players set updated_at=:ts, possible_ban=:possible_ban, confirmed_ban=:confirmed_ban, confirmed_player=:confirmed_player, label_id=:label_id where id=:player_id;'
    param = {
        'ts':  time.strftime('%Y-%m-%d %H:%M:%S'),
        'possible_ban': possible_ban,
        'confirmed_ban': confirmed_ban,
        'confirmed_player': confirmed_player,
        'label_id': label_id,
        'player_id': player_id
    }
    execute_sql(sql_update, param=param, debug=debug, has_return=False)


def get_token(token):
    sql = 'select * from Tokens where token=:token;'
    param = {
        'token': token
    }
    return execute_sql(sql, param=param, debug=False, has_return=True)


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def create_token(player_name, highscores, verify_ban):
    sql_insert = 'insert into Tokens (player_name, request_highscores, verify_ban, token) values (:player_name, :highscores, :verify_ban, :token);'
    token = get_random_string(15)
    param = {
        'player_name': player_name,
        'highscores': highscores,
        'verify_ban': verify_ban,
        'token': token
    }
    execute_sql(sql_insert, param=param, debug=False, has_return=False)
    return token


def get_highscores_data():
    sql_highscores = 'select a.*,b.name from playerHiscoreData a left join Players b on (a.Player_id = b.id);'
    highscores = execute_sql(sql_highscores, param=None,
                             debug=False, has_return=True)
    return highscores


def get_player_names():
    sql = 'select * from Players;'
    data = execute_sql(sql, param=None, debug=False, has_return=True)
    return data


def get_player_labels():
    sql = 'select * from Labels;'
    data = execute_sql(sql, param=None, debug=False, has_return=True)
    return data


def get_number_confirmed_bans():
    sql = 'SELECT COUNT(*) bans FROM Players WHERE confirmed_ban = 1;'
    data = execute_sql(sql, param=None, debug=False, has_return=True)
    return data[0].bans


def get_report_stats():
    sql = '''
        SELECT
            sum(bans) bans,
            sum(false_reports) false_reports,
            sum(bans) + sum(false_reports) total_reports,
            sum(bans)/ (sum(bans) + sum(false_reports)) accuracy
        FROM (
            SELECT 
                confirmed_ban,
                sum(confirmed_ban) bans,
                sum(confirmed_player) false_reports
            FROM Players
            GROUP BY
                confirmed_ban
            ) a;
    '''
    data = execute_sql(sql, param=None, debug=False, has_return=True)
    return data


def get_number_tracked_players():
    sql = 'SELECT COUNT(*) count FROM Players;'
    data = execute_sql(sql, param=None, debug=False, has_return=True)
    return data

#TODO: use contributor
def get_contributions(contributor):

    query= '''
        SELECT 
            rptr.name reporter_name,
            rptd.name reported_name,
            rptd.confirmed_ban
        from Reports rpts
        inner join Players rptr on(rpts.reportingID = rptr.id)
        inner join Players rptd on(rpts.reportedID = rptd.id)
        WHERE 1=1
        	and rptr.name = :contributor
    '''

    params = {
        "contributor": contributor
    }

    data = execute_sql(query, param=params, debug=False, has_return=True)

    return data


#TODO: route & visual on website
def get_player_table_stats():
    sql = ''' 
        SELECT 
            count(*) Players_checked, 
            Date(updated_at) last_checked_date
        FROM `Players` 
        GROUP BY
            Date(updated_at)
        order BY
            Date(updated_at) DESC
    '''
    data = execute_sql(sql, param=None, debug=False, has_return=True)
    return data

#TODO: route & visual on website
def get_hiscore_table_stats():
    sql = ''' 
        SELECT 
            count(*) hiscore_Players_checked, 
            Date(timestamp) hiscore_checked_date
        FROM playerHiscoreData
        GROUP BY
            Date(timestamp)
        order BY
            Date(timestamp) DESC;
    '''
    data = execute_sql(sql, param=None, debug=False, has_return=True)
    return data