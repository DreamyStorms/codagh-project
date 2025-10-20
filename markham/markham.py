import os
import sys
import sqlite3
from pathlib import Path
from pathlib import PurePath
import chess
import chess.pgn


def select_games(pgn_path, min_rating):
    path = PurePath(pgn_path)
    pgn = open(path)

    con = sqlite3.connect(Path('lib') / 'data' / 'pgn' / (path.stem + ".db"))
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

def pgn_to_fen(game_dir): # Takes in directory to .pgn and returns a list of [board position, move]
    pgn = open(game_dir)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    fen = []

    for move in game.mainline_moves():
        fen.append((board.fen(), move.uci()))
        board.push(move)
    return fen

def db_table_exist(cur, name):
    res = cur.execute(f"SELECT name FROM sqlite_master WHERE type ='table' and name = '{name}'")
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
        case "select-games":
            select_games(sys.argv[2], sys.argv[3])
        case "clear-selected":
            pass
        case "parse-selected":
            pass

    
    
main()