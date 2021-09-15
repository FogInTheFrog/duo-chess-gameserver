from datetime import datetime
from enum import Enum
from typing import Optional
from app.engine.chessEngine import GameState
from sqlalchemy.orm import Session
import re
import app.engine.chessEngine as engine
import pika
import json

DEFAULT_PACE = 180


class Result(Enum):
    white = int(0)
    black = int(1)
    draw = int(2)
    no_result = int(400)


class PlayerByTable:
    def __init__(self, user_nick: str, token: str, clock_time: int = DEFAULT_PACE, player_id: Optional[int] = -1):
        self.nickname = user_nick
        self.token = token
        self.time_left = clock_time
        self.player_id = player_id


class Table:
    def __init__(self, game_state: engine.GameState,
                 table_id: Optional[int] = -1, half_moves: Optional[int] = 0,
                 pbt1: Optional[PlayerByTable] = None,
                 pbt2: Optional[PlayerByTable] = None,
                 pbt3: Optional[PlayerByTable] = None,
                 pbt4: Optional[PlayerByTable] = None,
                 game_start_time: Optional[str] = None,
                 last_move_time: Optional[str] = None,
                 result: Optional[Result] = Result.no_result):
        self.table_id = table_id
        self.game_state = game_state
        self.half_moves = half_moves
        self.result = result
        self.white_one_PBT: PlayerByTable = pbt1
        self.white_two_PBT: PlayerByTable = pbt2
        self.black_one_PBT: PlayerByTable = pbt3
        self.black_two_PBT: PlayerByTable = pbt4
        self.game_start_time = datetime.fromisoformat(game_start_time)
        self.last_move_time = datetime.fromisoformat(last_move_time)

    def get_param_list(self):
        params_list = [self.table_id, self.game_state.game_state_to_fen(), self.half_moves,
                       self.result, self.game_start_time.isoformat(),
                       self.last_move_time.isoformat()]
        wtm_nickname = self.who_to_move()
        pbt_list = [self.white_one_PBT, self.white_two_PBT, self.black_one_PBT,
                    self.black_two_PBT]

        for pbt in pbt_list:
            if pbt is not None:
                if pbt.nickname == wtm_nickname:
                    params_list.append(pbt)
        return params_list

    def who_to_move(self) -> str:
        players_list_order = [self.white_one_PBT, self.black_one_PBT,
                              self.white_two_PBT, self.black_two_PBT]
        return players_list_order[self.half_moves % 4].nickname

    def get_number_of_players(self):
        num = 0
        num += self.white_one_PBT is not None
        num += self.white_two_PBT is not None
        num += self.black_one_PBT is not None
        num += self.black_two_PBT is not None
        return num

    def add_player(self, nickname: str, token: str, db: Session):
        pbt_list = [self.white_one_PBT, self.white_two_PBT,
                    self.black_one_PBT, self.black_two_PBT]

        # check for unique nickname
        for pbt in pbt_list:
            if pbt is not None:
                if pbt.nickname == nickname:
                    return False

        if self.white_one_PBT is None:
            self.white_one_PBT = PlayerByTable(nickname, token, DEFAULT_PACE)
            return add_player_to_table_db(self.table_id, nickname, token, 0, db)

        if self.white_two_PBT is None:
            self.white_two_PBT = PlayerByTable(nickname, token, DEFAULT_PACE)
            return add_player_to_table_db(self.table_id, nickname, token, 1, db)

        if self.black_one_PBT is None:
            self.black_one_PBT = PlayerByTable(nickname, token, DEFAULT_PACE)
            return add_player_to_table_db(self.table_id, nickname, token, 2, db)

        if self.black_two_PBT is None:
            self.black_two_PBT = PlayerByTable(nickname, token, DEFAULT_PACE)
            return add_player_to_table_db(self.table_id, nickname, token, 3, db)

        return False

    def is_this_player_by_table(self, nickname: str, token: str):
        player_list = [self.white_one_PBT, self.white_two_PBT, self.black_one_PBT, self.black_two_PBT]

        for player in player_list:
            if player.nickname == nickname and player.token == token:
                return True
        print("Player is not by the table")
        return False

    def validate_whether_player_can_move(self, nickname: str, token: str) -> bool:
        if self.is_this_player_by_table(nickname, token):
            if self.who_to_move() == nickname:
                if self.result == Result.no_result or self.result == 400:
                    return True
        print("Player cannot move ", nickname, self.who_to_move())
        return False

    def start_game(self, db: Session):
        if self.get_number_of_players() < 4:
            return False

        self.game_start_time = datetime.now()
        self.last_move_time = datetime.now()
        print("GAME NUMBER " + str(self.table_id) + " STARTED", self.last_move_time.__repr__())
        start_game_in_db(self.table_id, db)
        return True

    def get_pbt_by_nickname(self, nickname: str):
        pbts_list = [self.white_one_PBT, self.white_two_PBT,
                     self.black_one_PBT, self.black_two_PBT]

        for x in pbts_list:
            if x.nickname == nickname:
                return x

    def get_result_color_by_nickname_of_player_flagged(self, nickname: str):
        if nickname == self.white_one_PBT.nickname or nickname == self.white_two_PBT.nickname:
            return Result.black
        if nickname == self.black_one_PBT.nickname or nickname == self.black_two_PBT.nickname:
            return Result.white
        return Result.no_result

    def update_players_times(self):
        pbt_list = [self.white_one_PBT, self.white_two_PBT,
                    self.black_one_PBT, self.black_two_PBT]
        wtm_nickname = self.who_to_move()

        for pbt in pbt_list:
            if pbt is not None:
                if pbt.nickname == wtm_nickname:
                    time_now = datetime.now()
                    time_delta = (time_now - self.last_move_time)
                    elapsed_seconds = time_delta.total_seconds()

                    pbt.time_left -= int(elapsed_seconds)
                    self.last_move_time = datetime.now()

    # updates times
    def move(self, nickname: str, token: str, move_string: str, db: Session) -> bool:
        if self.validate_whether_player_can_move(nickname, token):
            game_state = self.game_state
            start = (int(move_string[0]), int(move_string[1]))
            end = (int(move_string[2]), int(move_string[3]))
            pbt = self.get_pbt_by_nickname(nickname)

            if game_state.move(start, end):
                self.update_players_times()

                if pbt.time_left < 0:
                    self.result = self.get_result_color_by_nickname_of_player_flagged(nickname)

                params_list = self.get_param_list()
                update_db_after_move(params_list, db)
                return True
        return False

    def update_leaderboard(self):
        credentials = pika.PlainCredentials('rabbit', 'HyLU1eKw42oI')
        parameters = pika.ConnectionParameters('34.118.13.126', 5672, '/', credentials, heartbeat=0)
        rabbit_connection = pika.BlockingConnection(parameters)
        channel = rabbit_connection.channel()
        channel.exchange_declare(exchange='message-exchange', exchange_type='fanout')
        channel.queue_declare(queue='update-leaderboard', durable=True)
        channel.queue_bind(exchange='message-exchange', queue='update-leaderboard')

        print("UPDATING LEADERBOARD")
        pbts = [self.white_one_PBT, self.white_two_PBT,
                self.black_one_PBT, self.black_two_PBT]
        for pbt in pbts:
            if self.did_nickname_won(pbt.nickname):
                data = {'nickname': pbt.nickname, 'result': 'won'}
                channel.basic_publish(exchange='message-exchange',
                                      routing_key='update-leaderboard',
                                      body=json.dumps(data))
                print(" [x] Sent %r'", json.dumps(data))
            elif self.did_nickname_drawn(pbt.nickname):
                data = {'nickname': pbt.nickname, 'result': 'draw'}
                channel.basic_publish(exchange='message-exchange',
                                      routing_key='update-leaderboard',
                                      body=json.dumps(data))
                print(" [x] Sent %r'", json.dumps(data))
            elif self.did_nickname_lost(pbt.nickname):
                data = {'nickname': pbt.nickname, 'result': 'lost'}
                channel.basic_publish(exchange='message-exchange',
                                      routing_key='update-leaderboard',
                                      body=json.dumps(data))
                print(" [x] Sent %r'", json.dumps(data))
            else:
                print(pbt.nickname, "dont have result")

    def is_game_over(self) -> bool:
        if self.last_move_time is not None:
            time_elapsed = (datetime.now() - self.last_move_time).total_seconds()
            if time_elapsed >= 5:
                self.update_players_times()

        if self.result != Result.no_result and self.result != 400:
            return True

        pbt_list = [self.white_one_PBT, self.white_two_PBT, self.black_two_PBT, self.black_one_PBT]
        for pbt in pbt_list:
            if pbt is not None:
                if pbt.time_left < 0:
                    self.result = self.get_result_color_by_nickname_of_player_flagged(pbt.nickname)
                    self.update_leaderboard()
                    return True

        if self.game_state.is_game_over():
            score = self.game_state.get_result()
            self.result = Result(score)
            self.update_leaderboard()
            self.result = score
            return True
        return False

    def get_result_of_game(self) -> int:
        self.is_game_over()
        result = self.result
        if type(result) == Result:
            return result.value
        return result

    # Following methods assume nickname exists in game
    def did_nickname_won(self, nickname: str) -> bool:
        if self.result == Result.no_result or self.result == Result.draw:
            return False

        if self.result == Result.white:
            if nickname == self.white_one_PBT.nickname or \
                    nickname == self.white_two_PBT.nickname:
                return True

        if self.result == Result.black:
            if nickname == self.black_one_PBT.nickname or \
                    nickname == self.black_two_PBT.nickname:
                return True
        return False

    def did_nickname_drawn(self, nickname: str) -> bool:
        if self.result == Result.draw:
            players_list = [self.white_one_PBT, self.white_two_PBT,
                            self.black_one_PBT, self.black_two_PBT]
            if nickname in players_list:
                return True
        return False

    def did_nickname_lost(self, nickname: str) -> bool:
        if self.result == Result.no_result or self.result == Result.draw:
            return False

        if self.result == Result.black:
            if nickname == self.white_one_PBT.nickname or \
                    nickname == self.white_two_PBT.nickname:
                return True

        if self.result == Result.white:
            if nickname == self.black_one_PBT.nickname or \
                    nickname == self.black_two_PBT.nickname:
                return True
        return False

    # Returns JSON
    def get_times(self):
        nickname_to_move = self.who_to_move()

        pbt_list = [self.white_one_PBT, self.white_two_PBT, self.black_one_PBT, self.black_two_PBT]
        times = {}
        for pbt in pbt_list:
            if pbt is not None:
                if pbt.nickname == nickname_to_move and self.get_number_of_players() == 4:
                    time_now = datetime.now()
                    time_delta = (time_now - self.last_move_time)
                    elapsed_seconds = time_delta.total_seconds()
                    times[pbt.nickname] = pbt.time_left - elapsed_seconds
                else:
                    times[pbt.nickname] = pbt.time_left
        return times


def get_table_by_id(table_id: int, db: Session) -> Table:
    return get_table_by_id_db(table_id, db)


def create_new_table(nickname: str, token: str, db: Session):
    new_game_state = engine.GameState()
    new_game_state_fen = new_game_state.game_state_to_fen()
    game_id = create_game_db(nickname, token, DEFAULT_PACE, new_game_state_fen, db)

    return game_id


# Returns player id in db
def add_player_db(nickname: str, token: str, pace: int, db: Session) -> int:
    db.execute(
        f"INSERT INTO players (nickname, token, time_left) VALUES ('{nickname}', '{token}', '{pace}')"
    )
    db.commit()
    return get_player_id_from_db(nickname, token, db)


def get_player_id_from_db(nickname: str, token: str, db: Session) -> int:
    is_in_db = db.execute(
        f"SELECT player_id FROM players WHERE nickname = :nickname AND token = :token",
        {'nickname': nickname, 'token': token}
    ).fetchone()

    if is_in_db is None:
        return -1

    return int(re.sub('[^0-9]', '', str(is_in_db)))


def create_game_db(nickname: str, token: str, pace: int, fen: str, db: Session) -> int:
    # check if player in DB
    player_id = get_player_id_from_db(nickname, token, db)
    if player_id is not -1:
        return -1
    add_player_db(nickname, token, pace, db)

    time_now = datetime.now()
    iso_time = time_now.isoformat()
    data = db.execute(
        f"SELECT player_id FROM players WHERE nickname = :nickname AND token = :token",
        {'nickname': nickname, 'token': token}
    ).fetchone()

    res = db.execute(
        "INSERT INTO games (white_one_id, white_two_id, black_one_id, black_two_id, halfmoves, "
        "result, game_start_time, last_move_time, fen) VALUES (:woid, :wtid, :boid, :btid, "
        ":halfmoves, :result, :start_time, :last_move_time, :fen) RETURNING game_id",
        {'woid': data[0], 'wtid': -1, 'boid': -1, 'btid': -1, 'halfmoves': 0, 'result': 400,
         'start_time': str(iso_time), 'last_move_time': str(iso_time), 'fen': str(fen)}
    )
    db.commit()
    game_id_str = res.fetchone()
    return int(re.sub('[^0-9]', '', str(game_id_str)))


def get_table_by_id_db(table_id: int, db: Session):
    data = db.execute(
        "SELECT game_id, white_one_id, white_two_id, black_one_id, black_two_id, halfmoves, "
        "result, game_start_time, last_move_time, fen FROM "
        "games WHERE game_id = :table_id", {'table_id': table_id}).fetchone()
    if data is None:
        return None
    print(data)
    loaded_game_state = GameState()
    loaded_game_state.load_game_state_from_fen(data[9])

    players_ids = [data[1], data[2], data[3], data[4]]
    pbt_list = []
    for player_id in players_ids:
        if player_id != -1:
            player_from_db = db.execute(
                "SELECT player_id, nickname, token, time_left FROM players WHERE player_id = :player_id",
                {'player_id': player_id}
            ).fetchone()
            pbt_list.append(PlayerByTable(player_from_db[1], player_from_db[2], player_from_db[3],
                                          player_from_db[0]))
        else:
            pbt_list.append(None)

    my_table = Table(loaded_game_state, data[0], data[5], pbt_list[0], pbt_list[1], pbt_list[2],
                     pbt_list[3], data[7], data[8], result=data[6])
    return my_table


def add_player_to_table_db(table_id: int, nickname: str, token: str, position: int, db: Session) -> bool:
    player_id = get_player_id_from_db(nickname, token, db)
    if player_id is not -1:
        return False
    player_id = add_player_db(nickname, token, DEFAULT_PACE, db)
    print("join table", player_id, table_id)
    if position == 0:
        db.execute("UPDATE games SET white_one_id = :new_value WHERE game_id = :table_id",
                   {'new_value': player_id, 'table_id': table_id})
        db.commit()
        return True
    elif position == 1:
        db.execute("UPDATE games SET white_two_id = :new_value WHERE game_id = :table_id",
                   {'new_value': player_id, 'table_id': table_id})
        db.commit()
        return True
    elif position == 2:
        db.execute("UPDATE games SET black_one_id = :new_value WHERE game_id = :table_id",
                   {'new_value': player_id, 'table_id': table_id})
        db.commit()
        return True
    elif position == 3:
        db.execute("UPDATE games SET black_two_id = :new_value WHERE game_id = :table_id",
                   {'new_value': player_id, 'table_id': table_id})
        db.commit()
        return True
    return False


def start_game_in_db(table_id: int, db: Session):
    time_now = datetime.now()
    iso_time_now = time_now.isoformat()
    db.execute(
        "UPDATE games SET game_start_time = :iso_t WHERE game_id = :table_id",
        {'iso_t': str(iso_time_now), 'table_id': table_id})
    db.execute(
        "UPDATE games SET last_move_time = :iso_t WHERE game_id = :table_id",
        {'iso_t': str(iso_time_now), 'table_id': table_id})
    db.commit()


def update_db_after_move(params_list, db: Session):
    table_id = params_list[0]
    fen = params_list[1]
    half_moves = params_list[2] + 1
    result = params_list[3]
    if type(result) == Result:
        result = result.value
    game_start_time = params_list[4]
    last_move_time = params_list[5]
    pbt_to_move = params_list[6]
    db.execute(
        "UPDATE players SET time_left = :time_left WHERE player_id = :player_id",
        {'time_left': pbt_to_move.time_left, 'player_id': pbt_to_move.player_id}
    )
    db.execute(
        "UPDATE games SET fen = :new_val WHERE game_id = :table_id",
        {'new_val': fen, 'table_id': table_id}
    )
    db.execute(
        "UPDATE games SET halfmoves = :new_val WHERE game_id = :table_id",
        {'new_val': half_moves, 'table_id': table_id}
    )
    db.execute(
        "UPDATE games SET result = :new_val WHERE game_id = :table_id",
        {'new_val': result, 'table_id': table_id}
    )
    db.execute(
        "UPDATE games SET game_start_time = :new_val WHERE game_id = :table_id",
        {'new_val': game_start_time, 'table_id': table_id}
    )
    db.execute(
        "UPDATE games SET last_move_time = :new_val WHERE game_id = :table_id",
        {'new_val': last_move_time, 'table_id': table_id}
    )
    db.commit()


def update_game_result(table_id: int, result: int, db: Session):
    db.execute(
        "UPDATE games SET result = :new_val WHERE game_id = :table_id",
        {'new_val': result, 'table_id': table_id}
    )
    db.commit()
