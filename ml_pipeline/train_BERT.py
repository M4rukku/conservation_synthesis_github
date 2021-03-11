from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import transformers
from sklearn import metrics
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from transformers import DistilBertTokenizerFast

#import the data
x_relevance_data_path = Path(".") / "ml_data" / "x_relevance_data_v1.pd.json"
y_relevance_data_path = Path(".") / "ml_data" / "y_relevance_data_v1.pd.json"
x_relevance_data = pd.read_json(x_relevance_data_path)
y_relevance_data = pd.read_json(y_relevance_data_path)

# data preprocessing
# concat the journal_name, title, abstract together to form input
# other development method could still existed but it would be hard to observe
x_relevance_data["input"] = x_relevance_data["title"].astype('str')+ ' ' + x_relevance_data["abstract"].astype('str')
df_train=pd.concat([x_relevance_data["input"],y_relevance_data["relevance"]],axis=1)

#split the data for training and testing
train_size = 0.7
train_dataset=df_train.sample(frac=train_size,random_state=0).reset_index(drop=True)
valid_dataset=df_train.drop(train_dataset.index).reset_index(drop=True)

# print(train_dataset.head())
# print(valid_dataset.head())

#setup the variable and parameters settings
MAX_LEN = 512 #NB this is to truncate everything after that!
BATCH_SIZE = 32*16
LEARNING_RATE = 1e-05
tokenizer = DistilBertTokenizerFast.from_pretrained(
    'distilbert-base-uncased',
    do_lower_case=True #note that the tokenizer only recongnize lower case character
)

#create dataloader for pytorch to train
class CE_Dataset(Dataset):
    def __init__(self, dataframe, tokenizer, max_len):
        self.data = dataframe
        self.tokenizer = tokenizer
        self.max_len = max_len
        
    def __getitem__(self, index):
        input = str(self.data.input[index])
        inputs = self.tokenizer.encode_plus(
            input,
            None,
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_token_type_ids=True
        )
        ids = inputs['input_ids']
        mask = inputs['attention_mask']
        return {
            'ids': torch.tensor(ids, dtype=torch.long),
            'mask': torch.tensor(mask, dtype=torch.long),
            'targets': torch.tensor(self.data.relevance[index], dtype=torch.float)
        }
        
    def __len__(self):
        return len(self.data)


# Creating the dataset and dataloader for the neural network
print("FULL Dataset: {}".format(df_train.shape))
print("TRAIN Dataset: {}".format(train_dataset.shape))
print("VALID Dataset: {}".format(valid_dataset.shape))

training_set = CE_Dataset(train_dataset, tokenizer, MAX_LEN)
validation_set = CE_Dataset(valid_dataset, tokenizer, MAX_LEN)

# print(training_set[0])

#setting up training and validation parameters
train_params = {'batch_size': BATCH_SIZE,
                'shuffle': True,
                'num_workers': 32,
                'pin_memory':True,
                }

valid_params = {'batch_size': BATCH_SIZE,
                'shuffle': True,
                'num_workers': 32,
                'pin_memory':True,
                }

train_dl = DataLoader(training_set, **train_params)
valid_dl = DataLoader(validation_set, **valid_params)

# Creating the simple model class
# we use a relatively simple architecture to fine tune: 
#Bert Encoder(pooled output) -> Dropout -> Linear layer -> Final Output

class DistillBERTClass(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.distill_bert = transformers.DistilBertModel.from_pretrained('distilbert-base-uncased')
        self.drop = torch.nn.Dropout(0.3) #p is a magic number
        self.out = torch.nn.Linear(768, 1)
    
    def forward(self, ids, mask):
        distilbert_output = self.distill_bert(ids, mask)
        hidden_state = distilbert_output[0]  # (bs, seq_len, dim)
        pooled_output = hidden_state[:, 0]  # (bs, dim)
        output_1 = self.drop(pooled_output)
        output = self.out(output_1)
        return output

#setting up the CUDA enviroment and use all avaliable GPU
device = torch.device('cuda')
#sending the model to the device with nn.DataParallel wraps around
model = torch.nn.DataParallel(DistillBERTClass(),device_ids=list(range(8))).to(device)

# print(model)

#loss functions
def loss_fn(outputs, targets):
    return nn.BCEWithLogitsLoss()(outputs, targets)
optimizer = torch.optim.Adam(params =  model.parameters(), lr=LEARNING_RATE)

#evaluation functions
def eval_fn(data_loader, model):
    model.eval()
    fin_targets = []
    fin_outputs = []
    with torch.no_grad():
        for bi, d in tqdm(enumerate(data_loader), total=len(data_loader)):
            ids = d["ids"]
            mask = d["mask"]
            targets = d["targets"]

            ids = ids.to(device, dtype=torch.long)
            mask = mask.to(device, dtype=torch.long)
            targets = targets.to(device, dtype=torch.float)

            outputs = model(ids=ids, mask=mask)
            fin_targets.extend(targets.cpu().detach().numpy().tolist())
            fin_outputs.extend(torch.sigmoid(outputs).cpu().detach().numpy().tolist())
        fin_outputs = np.array(fin_outputs) >= 0.5
        f1 = metrics.f1_score(fin_targets, fin_outputs)
    return f1

#training functions
def fit(num_epochs, model, loss_fn, opt, train_dl, valid_dl):
    for epoch in range(num_epochs):
        model.train()
        for _,data in enumerate(train_dl, 0):
            ids = data['ids'].to(device, dtype = torch.long)
            mask = data['mask'].to(device, dtype = torch.long)
            targets = data['targets'].to(device, dtype = torch.float)
            outputs = model(ids, mask).squeeze()
            loss = loss_fn(outputs, targets)
            loss.backward()
            opt.step()
            opt.zero_grad()

        valid_acc = eval_fn(valid_dl, model)
        print('Epoch [{}/{}], Train Loss: {:.4f} and Validation f1 {:.4f}'.format(epoch+1, num_epochs, loss.item(),valid_acc))
        torch.save(model, 'checkpoints_epoch' + str(epoch) + '.pth')


#train for 10 epoch to fine tune
fit(10, model, loss_fn, optimizer, train_dl,valid_dl)