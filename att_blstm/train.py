import json
import numpy as np
import torch
import torch.nn as nn
from torch import optim
import torch.utils.data as D

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from torchviz import make_dot

from att_blstm.Att_BLSTM import *


with open('D:/CAIL2018_ALL_DATA/att_blstm/open_data/open_data/word2idx','r',encoding='utf8') as w2ifile:
    word2id=json.load(w2ifile)

config={}
config['EMBEDDING_SIZE'] = len(word2id)+1
config['EMBEDDING_DIM'] = 200
config['POS_SIZE'] = 121
config['POS_DIM'] = 25
config['HIDDEN_DIM'] = 200
config['TAG_SIZE'] = 35
config['BATCH'] = 20
config["pretrained"]=True

learning_rate = 0.001


BATCH=config['BATCH']
EPOCHS=100


def get_position(original_position):
    pos=original_position+int(config['POS_SIZE']/2)
    if pos<0:pos=0
    elif pos>config['POS_SIZE']:pos=config['POS_SIZE']
    return pos

def prepare_word_embedding_matrix(word2id):
    embedding_pre = []

    word2vec = {}
    with open('D:/CAIL2018_ALL_DATA/att_blstm/open_data/open_data/word2vec', 'r', encoding='utf8') as input_data:
        for line in input_data.readlines():
            line = line.split()
            word2vec[line[0]] = line[1:]  # line shape: word dim1 dim2 ... dimN
            assert len(word2vec[line[0]]) == 200

    unknow_pre = []
    unknow_pre.extend([1] * 200) # unknown word has a special vector all dim equal to 1
    embedding_pre.append(unknow_pre)  # we use wordid 0 to represent unknown word
    for word in word2id:
        if word in word2vec:
            embedding_pre.append(word2vec[word])
        else:
            embedding_pre.append(unknow_pre)

    embedding_pre = np.asarray(embedding_pre, dtype="d")
    print("word embedding matrix shape:",embedding_pre.shape)

    return embedding_pre


def plot_grad_flow2(named_parameters):
    '''Plots the gradients flowing through different layers in the net during training.
    Can be used for checking for possible gradient vanishing / exploding problems.

    Usage: Plug this function in Trainer class after loss.backwards() as
    "plot_grad_flow(self.model.named_parameters())" to visualize the gradient flow'''
    ave_grads = []
    max_grads = []
    layers = []
    for n, p in named_parameters:
        if (p.requires_grad) and ("bias" not in n):
            layers.append(n)
            try:
                ave_grads.append(p.grad.abs().mean())
                max_grads.append(p.grad.abs().max())
            except AttributeError:
                ave_grads.append(0)
                max_grads.append(0)
    plt.bar(np.arange(len(max_grads)), max_grads, alpha=0.1, lw=1, color="c")
    plt.bar(np.arange(len(max_grads)), ave_grads, alpha=0.1, lw=1, color="b")
    plt.hlines(0, 0, len(ave_grads) + 1, lw=2, color="k")
    plt.xticks(range(0, len(ave_grads), 1), layers, rotation="vertical")
    plt.xlim(left=0, right=len(ave_grads))
    plt.ylim(bottom=-0.001, top=0.02)  # zoom in on the lower gradient regions
    plt.xlabel("Layers")
    plt.ylabel("average gradient")
    plt.title("Gradient flow")
    plt.grid(True)
    plt.legend([Line2D([0], [0], color="c", lw=4),
                Line2D([0], [0], color="b", lw=4),
                Line2D([0], [0], color="k", lw=4)], ['max-gradient', 'mean-gradient', 'zero-gradient'])
    plt.show()

def plot_grad_flow(named_parameters):
    ave_grads = []
    layers = []
    for n, p in named_parameters:
        if(p.requires_grad) and ("bias" not in n):
            layers.append(n)
            try:
                ave_grads.append(p.grad.abs().mean())
            except AttributeError:
                ave_grads.append(0)
    plt.plot(ave_grads, alpha=0.3, color="b")
    plt.hlines(0, 0, len(ave_grads)+1, linewidth=1, color="k" )
    plt.xticks(range(0,len(ave_grads), 1), layers, rotation="vertical")
    plt.xlim(xmin=0, xmax=len(ave_grads))
    plt.xlabel("Layers")
    plt.ylabel("average gradient")
    plt.title("Gradient flow")
    plt.grid(True)

def prepare_input_one_sentence(tokens,e1,e2):
    this = []
    thisPosition1 = []
    thisPosition2 = []

    words=tokens

    e1pos = -1
    e2pos = -1
    thisPos = 0
    for word in words:
        if word == e1:
            e1pos = thisPos
            this.append(word2id['李某'])
        elif word == e2:
            e2pos = thisPos
            this.append(word2id['李某'])
        else:
            if word in word2id:
                this.append(word2id[word])
            else:
                this.append(0)

        thisPos += 1

    thisPos = 0
    for word in words:
        thisPosition1.append(get_position(thisPos - e1pos))
        thisPosition2.append(get_position(thisPos - e2pos))
        thisPos += 1

    if len(this) > config['POS_SIZE'] / 2:
        this = this[:config['POS_SIZE'] + 1]
        thisPosition1 = thisPosition1[:config['POS_SIZE'] + 1]
        thisPosition2 = thisPosition2[:config['POS_SIZE'] + 1]
    elif len(this) < config['POS_SIZE'] / 2:
        original_len = len(this)
        this.extend([0] * (int(config['POS_SIZE'] / 2) - original_len))
        # print([0]*(int(config['POS_SIZE']/2)-len(this)))
        thisPosition1.extend([config['POS_SIZE'] - 1] * (int(config['POS_SIZE'] / 2) - original_len))
        # print([120]*(int(config['POS_SIZE']/2)-len(this)))
        thisPosition2.extend([config['POS_SIZE'] - 1] * (int(config['POS_SIZE'] / 2) - original_len))

    # print(this)
    # print(thisPosition1)

    return this,thisPosition1,thisPosition2

def prepare_training_set_from_cut(config):
    # print(word2id['李某'],word2id['王某'])
    train = []
    position1 = []
    position2 = []
    labels = []
    with open("D:/CAIL2018_ALL_DATA/att_blstm/open_data/open_data/cutsent_train_balanced.txt", "r", encoding="utf8") as cf:
        while True:
            this = []
            thisPosition1 = []
            thisPosition2 = []
            line = cf.readline()
            if not line: break
            article = json.loads(line)
            words = article['cut_text'].split()

            e1pos = -1
            e2pos = -1
            thisPos = 0
            for word in words:
                # if word in word2id:
                #     this.append(word2id[word])
                # else:
                #     this.append(0)
                #
                # if word == article['e1']:
                #     e1pos = thisPos
                # elif word == article['e2']:
                #     e2pos = thisPos
                if word == article['e1']:
                    e1pos = thisPos
                    this.append(word2id['李某'])
                elif word == article['e2']:
                    e2pos = thisPos
                    this.append(word2id['王某'])
                else:
                    if word in word2id:
                        this.append(word2id[word])
                    else:
                        this.append(0)

                thisPos += 1
            # print(this)
            thisPos = 0
            for word in words:
                thisPosition1.append(get_position(thisPos - e1pos))
                thisPosition2.append(get_position(thisPos - e2pos))
                thisPos += 1

            if len(this) > config['POS_SIZE'] / 2:
                this = this[:config['POS_SIZE'] + 1]
                thisPosition1 = thisPosition1[:config['POS_SIZE'] + 1]
                thisPosition2 = thisPosition2[:config['POS_SIZE'] + 1]
            elif len(this) < config['POS_SIZE'] / 2:
                original_len = len(this)
                this.extend([0] * (int(config['POS_SIZE'] / 2) - original_len))
                # print([0]*(int(config['POS_SIZE']/2)-len(this)))
                thisPosition1.extend([config['POS_SIZE'] - 1] * (int(config['POS_SIZE'] / 2) - original_len))
                # print([120]*(int(config['POS_SIZE']/2)-len(this)))
                thisPosition2.extend([config['POS_SIZE'] - 1] * (int(config['POS_SIZE'] / 2) - original_len))

            if len(train) == 0:
                print(this)
                print(thisPosition1)

            train.append(this)
            position1.append(thisPosition1)
            position2.append(thisPosition2)
            labels.append(int(article['tag']))

    return train,position1,position2,labels

def train(continue_from=0):
    if continue_from==0:
        net = Att_BLSTM(batch=config['BATCH'],
                        hidden_dim=config['HIDDEN_DIM'],
                        tag_size=config['TAG_SIZE'],
                        embedding_size=config['EMBEDDING_SIZE'],
                        embedding_dim=config['EMBEDDING_DIM'],
                        position_size=config['POS_SIZE'],
                        position_dim=config['POS_DIM'],
                        pretrained_embeddings=prepare_word_embedding_matrix(word2id=word2id))


    # print([i for i in net.parameters()])
    else:
        net = torch.load('model4_%d.pkl'%continue_from)
    optimizer = optim.Adam(net.parameters(), lr=learning_rate, weight_decay=1e-5)
    criterion = nn.CrossEntropyLoss(reduction='mean')  # size_average=True)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print("Device", device)
    net.to(device)

    net.device = device

    train, position1, position2, labels = prepare_training_set_from_cut(config)
    train, position1, position2 = np.asarray(train), np.asarray(position1), np.asarray(position2)

    train = torch.LongTensor(train[:len(train) - len(train) % BATCH])  # , requires_grad=True)
    position1 = torch.LongTensor(position1[:len(train) - len(train) % BATCH])  # , requires_grad=True)
    position2 = torch.LongTensor(position2[:len(train) - len(train) % BATCH])  # , requires_grad=True)
    labels = torch.LongTensor(labels[:len(train) - len(train) % BATCH])  # , requires_grad=True)

    train_datasets = D.TensorDataset(train, position1, position2, labels)
    train_dataloader = D.DataLoader(train_datasets, BATCH, True, num_workers=1)

    for epoch in range(continue_from,EPOCHS):
        print("epoch:", epoch)
        acc = 0
        total = 0

        positive=0
        true_positive=0

        for sentence, pos1, pos2, tags in train_dataloader:
            # sentence = Variable(sentence)
            # pos1 = Variable(pos1)
            # pos2 = Variable(pos2)
            # tags = Variable(tag)

            sentence, pos1, pos2, tags = sentence.to(device), pos1.to(device), pos2.to(device), tags.to(device)

            y = net(sentence, pos1, pos2)

            loss = criterion(y, tags)
            optimizer.zero_grad()
            loss.backward()

            # make_dot(y.mean(),params=dict(net.named_parameters())).render('test.gv', view=True)
            # plot_grad_flow2(net.named_parameters())
            #print("drawed")
            # plt.draw()
            optimizer.step()

            y = np.argmax(y.data.cpu().numpy(), axis=1)

            for y1, y2 in zip(y, tags):
                if y1 == y2:
                    acc += 1
                    if y2!=0:
                        true_positive+=1
                if y2!=0:
                    positive+=1

                total += 1

        print("acc:", 100 * float(acc) / total, "%")
        print("recall:", 100 * float(true_positive) / positive, "%")
        print("positive",positive)
        print("true positive",true_positive)
        # print(embedding_pre)
        #
        # em=nn.Embedding.from_pretrained(torch.FloatTensor(embedding_pre),freeze=False)
        #
        # print(em(torch.LongTensor([1,3,5])))
        if epoch % 1 == 0:
            torch.save(net, "model4_%d.pkl" % epoch)
            print("model has been saved")

def predict(sentence,e1,e2):
    with open("open_data/open_data/id2relation.json","r",encoding="utf8") as jf:
        id2r=json.load(jf)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print("Device", device)

    sentence=sentence.split()
    sentence,pos1,pos2=prepare_input_one_sentence(sentence,e1,e2)
    sentence,pos1,pos2=np.asarray([sentence]),np.asarray([pos1]),np.asarray([pos2])
    sentence,pos1,pos2=torch.LongTensor(sentence).to(device),torch.LongTensor(pos1).to(device),torch.LongTensor(pos2).to(device)

    net = torch.load('model4_36.pkl')

    net.batch=1

    y=net(sentence,pos1,pos2)

    y = np.argmax(y.data.cpu().numpy(), axis=1)

    return (id2r[str(y[0])])
if __name__ == "__main__":
    # print(predict("李某 与 其 姐姐 李1某 里应外合 ， 趁机 盗走 店 内 人民币 2000元","李某","李1某"))
    train()