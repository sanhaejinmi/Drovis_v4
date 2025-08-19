import torch
import torch.nn as nn


class LSTMModel(nn.Module):
    def __init__(self, input_size=66, hidden_size=64, num_layers=1, num_classes=4):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, 32)
        self.fc2 = nn.Linear(32, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = torch.relu(self.fc1(out))
        out = self.fc2(out)
        return out
