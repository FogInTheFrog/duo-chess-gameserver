DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS players;

CREATE TABLE IF NOT EXISTS games (
    "game_id" SERIAL,
    "white_one_id" integer,
    "white_two_id" integer,
    "black_one_id" integer,
    "black_two_id" integer,
    "halfmoves" integer,
    "result" integer,
    "game_start_time" VARCHAR(300),
    "last_move_time" VARCHAR(300),
    "fen" VARCHAR(300)
);

ALTER TABLE games
    ADD CONSTRAINT pk_games PRIMARY KEY ("game_id");

CREATE TABLE IF NOT EXISTS players (
    "player_id" SERIAL,
    "nickname" character varying(100),
    "token" character varying(256),
    "time_left" integer
);

ALTER TABLE players
    ADD CONSTRAINT pk_players PRIMARY KEY ("player_id");
