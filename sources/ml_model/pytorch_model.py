import torch
from transofmrers import DistilBertTokenizerFast,DistilBertModel
from pathlib import Path

class DistillBERTClass(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.distill_bert = DistilBertModel.from_pretrained('distilbert-base-uncased')
        self.drop = torch.nn.Dropout(0.3) #p is a magic number
        self.out = torch.nn.Linear(768, 1)
    
    def forward(self, ids, mask):
        distilbert_output = self.distill_bert(ids, mask)
        hidden_state = distilbert_output[0]  # (bs, seq_len, dim)
        pooled_output = hidden_state[:, 0]  # (bs, dim)
        output_1 = self.drop(pooled_output)
        output = self.out(output_1)
        return output

class PytorchModel:
    def __init__(self,model_class=DistilBertModel):
        #setup codde for inference
        self.max_len=512
        self.tokenizer=DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased', do_lower_case=True) #note that the tokenizer only recongnize lower case character
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.checkpoint=torch.load(Path('.')/"ml_model_checkpoints"/"checkpoints_epoch9.pth")
        self.model=model_class
        self.model.load_state_dict(self.checkpoint['model_state_dict'])
        self.model.eval()
        
    def do_prediction(self, title, journal_name, abstract):
        max_len = 512
        text = str(title) + " " + str(abstract)
        inputs = self.tokenizer.encode_plus(
            text,
            None,
            add_special_tokens=True,
            max_length=max_len,
            padding="max_length",
            truncation=True
        )

        ids = inputs["input_ids"]
        mask = inputs["attention_mask"]

        ids = torch.tensor(ids, dtype=torch.long).unsqueeze(0)
        mask = torch.tensor(mask, dtype=torch.long).unsqueeze(0)

        ids = ids.to(self.device, dtype=torch.long)
        mask = mask.to(self.device, dtype=torch.long)

        outputs = self.model(ids=ids, mask=mask)

        outputs = torch.sigmoid(outputs).cpu().detach().numpy()
        return outputs[0][0] > 0.5

    