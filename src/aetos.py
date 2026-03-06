import torch
from tqdm import tqdm
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, random_split
from torch.profiler import profile, ProfilerActivity, record_function
from devera import ChessMovesDataset

print(torch.accelerator.device_count())
device = torch.cuda.is_available() if torch.accelerator.is_available() else "cpu"
print(f"Using {device} device")


class MovePredicionNet(nn.Module):
    def __init__(self):
        super(MovePredicionNet, self).__init__()
        self.conv1 = nn.Conv2d(15, 16, 2)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 5, 2)
        self.fc1 = nn.LazyLinear(5)
        self.fc2 = nn.LazyLinear(6)
        self.fc3 = nn.LazyLinear(8 * 8 * 11 * 8)

    def forward(self, inputs):
        x = inputs["position"]
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = x.flatten()
        x = self.fc3(x)
        x = x.view(8, 8, 11, 8) * inputs["legal_moves"]
        x = F.softmax(x, dim=0)
        return x
    

learning_rate = 1e-3
batch_size = 256
epochs = 5


net = MovePredicionNet()
dataset = ChessMovesDataset("lib/data/data.db")
train_dataloader = DataLoader(dataset, batch_size=batch_size)
#test_dataloader = DataLoader(dataset, batch_size=batch_size)



criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=learning_rate, momentum=0.9)

def train_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    # Set the model to training mode - important for batch normalization and dropout layers
    # Unnecessary in this situation but added for best practices
    model.train()
    with profile(activities=[ProfilerActivity.CUDA, ProfilerActivity.CPU], record_shapes=True) as prof:
        with record_function("loop"):
            for batch, data in enumerate(dataloader):
                # Compute prediction and loss
                
                with record_function("model_inference"):
                    pred = model(data)
                loss = loss_fn(pred, data["move"])

                # Backpropagation
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()

                if batch % 100 == 0:
                    loss, current = loss.item(), batch * batch_size + batch_size
                    print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")
                    print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))

def test_loop(dataloader, model, loss_fn):
    # Set the model to evaluation mode - important for batch normalization and dropout layers
    # Unnecessary in this situation but added for best practices
    model.eval()
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct = 0, 0

    # Evaluating the model with torch.no_grad() ensures that no gradients are computed during test mode
    # also serves to reduce unnecessary gradient computations and memory usage for tensors with requires_grad=True
    with torch.no_grad():
        for data in dataloader:
            with profile(activities=[ProfilerActivity.CPU], record_shapes=True) as prof:
                with record_function("model_inference"):
                    pred = model(data)
            test_loss += loss_fn(pred, data["move"]).item()
            correct += (pred.argmax(1) == data["move"]).type(torch.float).sum().item()

    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")

for t in range(epochs):
    print(f"Epoch {t+1}\n-------------------------------")
    train_loop(train_dataloader, net, criterion, optimizer)
    #test_loop(test_dataloader, net, criterion)

print('Finished Training')