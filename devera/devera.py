from tensor_chess import Position
import numpy as np
import torch
import sqlite3

from torch.utils.data import Dataset

class ChessMovesDataset(Dataset):
    def __init__(self, db_path, transform=None):
        self.db_con = sqlite3.connect(db_path)
        self.transform = transform
    
    def __len__(self):
        cur = self.db_con.cursor()
        res = cur.execute("SELECT COUNT(*) from raw")
        return res.fetchone()[0]
    
    def __getitem__(self, index):
        cur = self.db_con.cursor()
        res = cur.execute(f"SELECT * FROM raw LIMIT 1 OFFSET {index}")
        fen, uci = res.fetchone()

        position = Position(fen)
        color_to_play = position.side_to_move
        deserialized_position = np.frombuffer(position.to_tensor(), np.int8)
        position_ndarray = np.reshape(deserialized_position, (15,8,8))

        move_square_from = uci_column_lookup[uci[0]] + uci_row_lookup[uci[1]]
        move_square_to = uci_column_lookup[uci[2]] + uci_row_lookup[uci[3]]
        move_promotion_piece = 0
        match len(uci):
            case 5:
                move_promotion_piece = uci_piece_lookup[uci[4]]

        match color_to_play:
            case 0:
                flipped_moves = position.generate_legal_moves()
            case 1:
                flipped_moves = []
                for move in position.generate_legal_moves():
                    flipped_moves.append(((63 - move[0]), (63 - move[1]), move[2], move[3]))

                position_ndarray = np.flip(position_ndarray, 1)
                position_ndarray = np.flip(position_ndarray, 2)
                position_ndarray_flipped = position_ndarray.copy()
                for i in range(6):
                    position_ndarray_flipped[i], position_ndarray_flipped[i + 6] = position_ndarray[i + 6], position_ndarray[i]
                position_ndarray = position_ndarray_flipped

                move_square_from = 63 - move_square_from
                move_square_to = 63 - move_square_to

        legal_moves = np.zeros(dtype=np.int8, shape=(64,88))
        for move in flipped_moves:
            match move[3]:
                case 3:
                    legal_moves[move[0], (move[1] + 24)] = 1
                case 2:
                    legal_moves[move[0], (move[1] + 16)] = 1
                case 1:
                    legal_moves[move[0], (move[1] + 8)] = 1
                case _:
                    legal_moves[move[0], move[1]] = 1
        
        legal_moves = np.reshape(legal_moves, (8,8,11,8))
        
        played_move = np.zeros(dtype=np.int8, shape=(64,88))
        match move_promotion_piece:
            case 3:
                played_move[move_square_from, (move_square_to + 24)] = 1
            case 2:
                played_move[move_square_from, (move_square_to + 16)] = 1
            case 1:
                played_move[move_square_from, (move_square_to + 8)] = 1
            case _:
                played_move[move_square_from, move_square_to] = 1
        
        played_move = np.reshape(played_move, (8,8,11,8))

        return {"position": torch.from_numpy(position_ndarray), "move": torch.from_numpy(played_move), "legal_moves": torch.from_numpy(legal_moves)}



uci_column_lookup = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
uci_row_lookup = {"1": 0, "2": 8, "3": 16, "4": 24, "5": 32, "6": 40, "7": 48, "8": 56}
uci_piece_lookup = {"n": 1, "b": 2, "r": 3, "q": 4}
