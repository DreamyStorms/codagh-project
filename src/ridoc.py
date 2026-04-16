import numpy as np
from chess import Board
from tqdm import tqdm

def matrix_from_board(board: Board):
    matrix = np.zeros((14, 8, 8))
    piece_map = board.piece_map()

    for square, piece in piece_map.items():
        col, row = divmod(square, 8)
        piece_type = piece.piece_type - 1
        piece_color = 0 if piece.color else 6
        matrix[piece_type + piece_color, row, col] = 1
    legal_moves = board.legal_moves
    for move in legal_moves:
        matrix[12, divmod(move.from_square, 8)] = 1
        matrix[13, divmod(move.to_square, 8)] = 1
    return matrix

def generate_nn_input(games):
    number_of_moves = 0
    for game in tqdm(games):
        board = game.board()
        for move in game.mainline_moves():
            number_of_moves += 1
            board.push(move)


    positions = np.memmap(filename="../lib/data/npy/position.npy", dtype=np.float32, mode="w+", shape=(number_of_moves, 14, 8, 8))
    moves = np.memmap(filename="../lib/data/npy/moves.npy", dtype=np.float32, mode="w+", shape=(number_of_moves, 64, 64))

    i = 0
    for game in tqdm(games):
        board = game.board()
        for move in game.mainline_moves():
            positions[i] = matrix_from_board(board)
            moves[i][move.from_square][move.to_square] = 1
            i += 1
            board.push(move)
    
    return positions, moves

def generate_eval_lables(games):
    number_of_positions = 0
    for game in tqdm(games):
        board = game.board()
        for move in game.mainline_moves():
            number_of_positions += 1
            board.push(move)
    
    positions = np.memmap(filename="../lib/data/npy/eval_position.npy", dtype=np.float32, mode="w+", shape=(number_of_positions, 14, 8, 8))
    results = np.memmap(filename="../lib/data/npy/reults.npy", dtype=np.float32, mode="w+", shape=(number_of_positions, 1))
    i = 0
    for game in tqdm(games):
        board = game.board()

        match game.headers["Result"]:
            case "1-0":
                result = 1
            case "0-1":
                result = 0
            case _:
                result = 0.5
                
        for move in game.mainline_moves():
            positions[i] = matrix_from_board(board)
            results[i] = result
            i += 1
            board.push(move)
    
    return positions, results
    
