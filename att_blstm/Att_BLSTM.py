import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(1)

class Att_BLSTM(nn.Module):
    def __init__(self,batch,hidden_dim,tag_size,embedding_size,embedding_dim,position_size,position_dim,pretrained_embeddings=None,dropout_p=0.3):
        super(Att_BLSTM, self).__init__()

        self.device="cpu"

        self.batch = batch
        self.hidden_dim = hidden_dim
        self.tag_size = tag_size

        self.embedding_size = embedding_size
        self.embedding_dim = embedding_dim

        self.position_size = position_size
        self.posistion_dim = position_dim

        if pretrained_embeddings is not None:
            self.word_embeds = nn.Embedding.from_pretrained(torch.FloatTensor(pretrained_embeddings), freeze=True)
        else:
            self.word_embeds = nn.Embedding(self.embedding_size, self.embedding_dim)

        self.position1_embeds = nn.Embedding(self.position_size, self.posistion_dim)
        self.position2_embeds = nn.Embedding(self.position_size, self.posistion_dim)

        self.lstm = nn.LSTM(input_size=self.embedding_dim + self.posistion_dim * 2, hidden_size=self.hidden_dim // 2,
                            num_layers=1, bidirectional=True)

        self.dropout_lstm = nn.Dropout(p=dropout_p)

        self.hidden = self.init_hidden(self.device)

        self.att_weight = nn.Parameter(torch.randn(1, self.hidden_dim))

        self.att2relation=nn.Linear(self.hidden_dim,self.tag_size)

    def init_hidden(self,device):
        h,c=(torch.randn(2, self.batch, self.hidden_dim // 2),
                torch.randn(2, self.batch, self.hidden_dim // 2))
        h,c=h.to(device),c.to(device)
        return (h,c)

    def attention(self, H):
        M = torch.tanh(H) #shape:batch_size,dimentions,token_num
        batch_att_weight=self.att_weight.unsqueeze(-1).expand(1,self.hidden_dim,self.batch)
        batch_att_weight=torch.transpose(batch_att_weight,1,2)
        batch_att_weight=torch.transpose(batch_att_weight,0,1)
        a = F.softmax(torch.bmm(batch_att_weight, M), 2) #batch,1,hiddendim * batch,dim,tokennum=batch,1,tokennum
        a = torch.transpose(a, 1, 2)#batch,tokennum,1
        return torch.bmm(H, a)#batch_size,dimentions,token_num*batch,tokennum,1=batch,dimensions,1

    def forward(self, sentence, position1, position2):

        self.hidden = self.init_hidden(self.device)

        # print(self.word_embeds(sentence).shape) batch_size*token_num*dimensions
        # print(self.position1_embeds(position1).shape) batch_size*token_num*dimensions
        # print(self.position2_embeds(position2).shape) batch_size*token_num*dimensions
        embeds = torch.cat((self.word_embeds(sentence), self.position1_embeds(position1), self.position2_embeds(position2)), 2)

        embeds = torch.transpose(embeds, 0, 1) #shape: token_num*batch_size*dimentions

        lstm_out, self.hidden = self.lstm(embeds, self.hidden)

        lstm_out = torch.transpose(lstm_out, 0, 1)
        lstm_out = torch.transpose(lstm_out, 1, 2) #shape:batch_size,dimentions,token_num

        lstm_out = self.dropout_lstm(lstm_out)

        att_out = torch.tanh(self.attention(lstm_out))

        att_out=torch.transpose(att_out,1,2)

        relation=self.att2relation(att_out)

        res = F.softmax(relation, 2)

        return res.view(self.batch, -1)