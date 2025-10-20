import os
import sys
import sqlite3
from pathlib import Path
import chess
import chess.pgn

def pgn_to_fen(game_dir): # Takes in directory to .pgn and returns a list of [board position, move]
    pgn = open(game_dir)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    fen = []

    for move in game.mainline_moves():
        fen.append((board.fen(), move.uci()))
        board.push(move)
    return fen

def db_table_raw_exist(cur):
    res = cur.execute("SELECT name FROM sqlite_master WHERE type ='table' and name = 'raw'")
    if res.fetchone == None:
        return False
    else:
        return True

def main(): 
    con = sqlite3.connect(Path('lib') / 'data' / 'data.db')
    cur = con.cursor()
    if not db_table_raw_exist(cur):
        cur.execute("CREATE TABLE raw(board, move)")

    match len(sys.argv):
        case 1:
            raise TypeError("Markham takes 1 postional argument but none were given") #No path
        case 2:
            print(pgn_to_fen(sys.argv[1])) 
        case _:
            out_to_db = False
            folder_in = False

            for i in range(2, len(sys.argv) - 1):
                match sys.argv[i]:
                    case "-o":
                        out_to_db = True
                    case "-f":
                        folder_in = True
                    case _:
                        raise ValueError("Unknown argument " + "\"" + sys.argv[i] + "\"") #Argument not recognized
            if folder_in:
                raise NotImplementedError
            else:
                cur.executemany("INSERT INTO raw VALUES(?, ?)", pgn_to_fen(sys.argv[1]))
                con.commit()

main()