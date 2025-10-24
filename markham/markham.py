import sys
import sqlite3
from tqdm import tqdm
from tqdm import trange
from pathlib import Path
from pathlib import PurePath
import chess
import chess.pgn

def querry_response_yes(querry: str) -> bool:
    res = input(f"{querry} (y/N)\n")
    if res.casefold() == "yes" or res.casefold() == "y":
        return True
    else:
        return False

def path_is_file(path: str) -> bool:
    if not Path(path).is_file():
        return False
    else:
        return True

def connect_db_from_pgn_path(pgn_path: str) -> sqlite3.Connection: # Creates a db connection from the provided pgn path
    path_is_file(pgn_path)

    con = sqlite3.connect(Path('lib') / 'data' / 'pgn' / (PurePath(pgn_path).stem + ".db"))
    return con

def select_games(pgn_path: str, min_rating: int) -> None: # Creates a db with offsets form games above the minimum rating i the provided pgn
    pgn = open(pgn_path)

    con = connect_db_from_pgn_path(pgn_path)
    cur = con.cursor()
    if not db_table_exist(con, "all_games"):
        cur.execute("CREATE TABLE all_games(offset, white_elo, black_elo)")
    if not db_table_exist(con, "selected_games"):
        cur.execute("CREATE TABLE selected_games(offset)")
    
    if db_table_empty(con, "all_games"):
        print("Searching for games...")
        games_found = 0
        batch_size = 100000
        games_left_to_process = True
        while games_left_to_process:
            games_found += batch_size
            for i in trange(batch_size):
                offset = pgn.tell()
                headers = chess.pgn.read_headers(pgn)

                if headers is None:
                    games_left_to_process = False
                    games_found -= (batch_size - (i + 1))
                    break
                
                value = (offset, headers.get("WhiteElo", "?"), headers.get("BlackElo", "?"))
                cur.execute("INSERT INTO all_games VALUES(?, ?, ?)", value)

            con.commit()
            print(f"{games_found} games found.")

        print("")
    
    for row in tqdm(cur.execute("SELECT offset, white_elo, black_elo FROM all_games").fetchall()):
        if row[1] > min_rating and row[2] > min_rating:
            cur.execute(f"INSERT INTO selected_games VALUES({row[0]})")
    
    con.commit()
    res = cur.execute("SELECT COUNT (*) FROM selected_games")
    print(f"{res.fetchone()[0]} games selected.")
    
    return

def clear_db_table(db_con: sqlite3.Connection, table_name: str) -> None: # Clears a specified table in the provided db
    cur = db_con.cursor()
    
    cur.execute(f"DELETE FROM {table_name} WHERE 1=1")
    db_con.commit()

    return

def game_data(game: chess.pgn.Game) -> list[list[str, str]]: # Returns a 2d list of every board position and move
    board = game.board()

    data = []
    url = game.headers.get("Site")

    for move in game.mainline_moves():
        data.append((board.fen(), move.uci(), url))
        board.push(move)

    return data

def db_table_exist(con: sqlite3.Connection, table_name: str) -> bool: # Returns True if the table exists in the provided db
    cur = con.cursor()
    res = cur.execute(f"SELECT name FROM sqlite_master WHERE type ='table' and name = '{table_name}'")
    if res.fetchone() is None:
        return False
    else:
        return True

def db_table_empty(con: sqlite3.Connection, table_name: str) -> bool:
    if not db_table_exist(con, table_name):
        return True
    
    cur = con.cursor()
    res = cur.execute(f"SELECT * FROM {table_name} WHERE 1=1 LIMIT 1")
    if res.fetchone() is None:
        return True
    else:
        return False

def parse_selected_games(pgn_path: str, main_db_con: sqlite3.Connection):
    selected_games_db_con = connect_db_from_pgn_path(pgn_path)
    selected_games_db_cur = selected_games_db_con.cursor()
    main_db_cur = main_db_con.cursor()

    pgn = open(pgn_path)

    for row in tqdm(selected_games_db_cur.execute("SELECT offset FROM selected_games").fetchall()):
        pgn.seek(row[0])
        main_db_cur.executemany("INSERT INTO raw VALUES(?, ?, ?)", game_data(chess.pgn.read_game(pgn))) 
        main_db_con.commit()
        
    return

def main():
    con = sqlite3.connect(Path('lib') / 'data' / 'data.db')
    cur = con.cursor()
    if not db_table_exist(con, "raw"):
        cur.execute("CREATE TABLE raw(board, move, url)")
    
    if len(sys.argv) <= 2:
        raise TypeError("missing required argument \"operation\" (pos 1)")
    
    operation = sys.argv[1]

    match operation:
        case "select-games": # (path, minnimum_rating)
            if len(sys.argv) == 3:
                raise TypeError(("missing required argument \"min-rating\" (pos 3)"))
            elif len(sys.argv) == 2:
                raise TypeError(("missing required argument \"path\" (pos 2)"))

            path = sys.argv[2]
            min_rating = sys.argv[3]

            if not path_is_file(path):
                raise FileNotFoundError
            try:
                int(min_rating)
            except:
                raise TypeError("min-rating must be an int")
            
            selected_games_db_con = connect_db_from_pgn_path(path)
            
            if not db_table_empty(selected_games_db_con, "selected_games"):
                if not querry_response_yes(f"This will clear the selection for {PurePath(path).name} do you want to proceed?"):
                    print("Operation aborted")
                    return
                else:
                    clear_db_table(selected_games_db_con, "selected_games")
                    
            select_games(path, min_rating)

            return

        case "clear-selected":
            if len(sys.argv) == 2:
                raise TypeError(("missing required argument \"path\" (pos 2)"))
            
            path = sys.argv[2]

            if not path_is_file(path):
                raise FileNotFoundError
            
            selected_games_db_con = connect_db_from_pgn_path(path)
            if not db_table_exist(selected_games_db_con, "selected_games") or db_table_empty(selected_games_db_con, "selected_games"):
                print("No games selected from " + PurePath(path).name)
                return
            
            if not querry_response_yes("Are you sure?"):
                print("Operation aborted")
                return
            
            clear_db_table(selected_games_db_con, "selected_games")

            return

        case "parse-selected":
            if len(sys.argv) == 2:
                raise TypeError(("missing required argument \"path\" (pos 2)"))
            
            path = sys.argv[2]

            if not path_is_file(path):
                raise FileNotFoundError
            
            selected_games_db_con = connect_db_from_pgn_path(path)
            if not db_table_exist(selected_games_db_con, "selected_games") or db_table_empty(selected_games_db_con, "selected_games"):
                print("No games selected from " + PurePath(path).name)
                return
            
            parse_selected_games(path, con)

            return

main()