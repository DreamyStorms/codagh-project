import os
import sys
import sqlite3
import chess
import chess.pgn

def pgn_to_fen(game_dir): # Takes in directory to .pgn and returns a list of [board position, move]
    pgn = open(game_dir)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    fen = []

    for move in game.mainline_moves():
        fen.append([board.fen(), move.uci()])
        board.push(move)
    return fen

def main(): # Handels arguments and redirects to the specified operation 
    if len(sys.argv) == 1:
        print("ERROR: No arguments")

    operation = sys.argv[1]

    match operation:
        case "pgn-fen":
            if len(sys.argv) != 3:
                print("ERROR: Incrorect number of arguments")
                return 4
            else:
                print(pgn_to_fen(sys.argv[2]))
                return 2


print(main())