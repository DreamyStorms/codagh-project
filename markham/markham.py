import os
import sys
import sqlite3
from pathlib import Path
from pathlib import PurePath
import chess
import chess.pgn

def connect_db_from_pgn_path(pgn_path: str) -> sqlite3.Connection: # Creates a db connection from the provided pgn path
    path = PurePath(pgn_path)

    con = sqlite3.connect(Path('lib') / 'data' / 'pgn' / (path.stem + ".db"))
    return con

def select_games(pgn_path: str, min_rating: int) -> None: # Creates a db with offsets form games above the minimum rating i the provided pgn
    pgn = open(pgn_path)

    con = connect_db_from_pgn_path(pgn_path)
    cur = con.cursor()
    if not db_table_exist(cur, "selected_games"):
        cur.execute("CREATE TABLE selected_games(offset)")
    
    while True:
        offset = pgn.tell()

        headers = chess.pgn.read_headers(pgn)

        if headers is None:
            break

        if headers.get("WhiteElo") > min_rating and headers.get("BlackElo") > min_rating:
            cur.execute(f"INSERT INTO selected_games VALUES({offset})")
            con.commit()
    return

def clear_db_table(db_con: sqlite3.Connection, table_name: str) -> None: # Clears a specified table in the provided db
    cur = db_con.cursor
    return

def pgn_to_fen(game_dir): # Takes in directory to .pgn and returns a list of [board position, move]
    pgn = open(game_dir)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    fen = []

    for move in game.mainline_moves():
        fen.append((board.fen(), move.uci()))
        board.push(move)
    return fen

def db_table_exist(cur: sqlite3.Cursor, table_name: str) -> bool: # Returns True if the table exists in the provided db
    res = cur.execute(f"SELECT name FROM sqlite_master WHERE type ='table' and name = '{table_name}'")
    if res.fetchone() is None:
        return False
    else:
        return True
    
def cli():
    raise NotImplementedError


def main():
    con = sqlite3.connect(Path('lib') / 'data' / 'data.db')
    cur = con.cursor()
    if not db_table_exist(cur, "raw"):
        cur.execute("CREATE TABLE raw(board, move)")
    
    if len(sys.argv) < 2:
        cli()
        return
    
    operation = sys.argv[1]

    match operation:
        case "select-games": # (path, minnimum_rating)
            select_games(sys.argv[2], sys.argv[3])
        case "clear-selected":
            pass
        case "parse-selected":
            pass

main()