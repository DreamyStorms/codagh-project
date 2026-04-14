from torch.utils.data import Dataset
import torch

class ChessDataset(Dataset):

    def __init__(self, positions, moves):
        self.postions = positions
        self.moves = moves
    
    def __len__(self):
        return len(self.moves)
    
    def __getitem__(self, index):
        return torch.tensor(self.postions[index]), torch.tensor(self.moves[index])

class EvalDataset(Dataset):

    def __init__(self, positions, results):
        self.postions = positions
        self.results = results
    
    def __len__(self):
        return len(self.results)
    
    def __getitem__(self, index):
        return torch.tensor(self.postions[index]), torch.tensor(self.results[index])