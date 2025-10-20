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
    match len(sys.argv):
        case 1:
            raise TypeError("Markham takes 1 postional argument but none were given")
        case 2:
            print(pgn_to_fen(sys.argv[1]))
        case 3:
            raise NotImplementedError
        case _:
            raise TypeError("Markham takes 1 positional and 1 optional arguments but " + str(len(sys.argv)-1) + " were given")
    


main()