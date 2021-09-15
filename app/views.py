from fastapi.responses import JSONResponse
import app.game_server as gs
from .database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


# If player with such credentials does not exists in db, new player is created
@router.post("/tables/{table_id}")
def join_table(table_id: int, user_nickname: str, token: str, db: Session = Depends(get_db)):
    my_table = gs.get_table_by_id(table_id, db)
    if my_table is None:
        res = JSONResponse(status_code=404, content="Such table does not exist")
        return res

    if my_table.add_player(user_nickname, token, db) is True:
        data = "Successfully joined"
        if my_table.start_game(db):
            data += ", game started"

        res = JSONResponse(status_code=200, content=data)
        return res

    return JSONResponse(status_code=400, content="Table is either full or nickname not unique")


# Creates new game instance and returns game id
@router.post("/tables/create/")
def create_game(user_nickname: str, token: str, db: Session = Depends(get_db)):
    new_table_id = gs.create_new_table(user_nickname, token, db)
    if new_table_id is None:
        return JSONResponse(status_code=400, content="Unable to create new game")
    elif new_table_id == -1:
        return JSONResponse(status_code=401, content="Can't create game, you are already in game")
    else:
        return JSONResponse(status_code=200, content=str(new_table_id))


# Move_string is 4 character length string made out of digits [0-7]
@router.get("/tables/{table_id}/move/")
def move(table_id: int, nickname: str, token: str, move_string: str, db: Session = Depends(get_db)):
    db.begin()
    my_table = gs.get_table_by_id(table_id, db)
    if my_table is None:
        return JSONResponse(status_code=404, content="Such table does not exist")

    if my_table.move(nickname, token, move_string, db):
        return JSONResponse(status_code=200, content="OK")

    data = my_table.get_result_of_game()
    if data != 400:
        gs.update_game_result(table_id, data, db)

    return JSONResponse(status_code=400, content="Bad Request")


@router.get("/tables/{table_id}/fen/")
def get_fen(table_id: int, db: Session = Depends(get_db)):
    my_table = gs.get_table_by_id(table_id, db)
    if my_table is None:
        return JSONResponse(status_code=404, content="Such table does not exist")

    content = my_table.game_state.game_state_to_fen()
    return JSONResponse(status_code=200, content=content)


# Returns string of 4 integers split with spaces of white1, white2, black1, black2 times
@router.get("/tables/{table_id}/times")
def get_times(table_id: int, db: Session = Depends(get_db)):
    my_table = gs.get_table_by_id(table_id, db)
    if my_table is None:
        return JSONResponse(status_code=404, content="Such table does not exist")

    content = my_table.get_times()
    return JSONResponse(status_code=200, content=content)


# Returns result: 0 is white, 1 is black, 2 is draw, 400 no result
@router.get("/tables/{table_id}/result")
def get_result(table_id: int, db: Session = Depends(get_db)):
    db.begin()
    my_table = gs.get_table_by_id(table_id, db)
    if my_table is None:
        return JSONResponse(status_code=404, content="Such table does not exist")

    data = my_table.get_result_of_game()
    if data != 400:
        gs.update_game_result(table_id, data, db)
    db.commit()
    return JSONResponse(status_code=200, content=data)


# Returns nickname of player expected to move
@router.get("/tables/{table_id}/who")
def get_whos_turn(table_id: int, db: Session = Depends(get_db)):
    my_table = gs.get_table_by_id(table_id, db)
    if my_table is None:
        return JSONResponse(status_code=404, content="Such table does not exist")

    data = {'nickname': my_table.who_to_move()}
    if data['nickname'] is None or my_table.get_number_of_players() < 4:
        return JSONResponse(status_code=400, content="Game hasn't started")

    return JSONResponse(status_code=200, content=data)
