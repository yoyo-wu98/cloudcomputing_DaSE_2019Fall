import os
import datetime
import csv
# import tqdm
import math
import numpy as np
import pandas as pd
import json

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

import data_loader
# train_file = "Gowalla_totalCheckins.txt"

ftype = torch.cuda.FloatTensor
ltype = torch.cuda.LongTensor

# Model Hyperparameters
dim = 13    # dimensionality
ww = 360  # winodw width (6h)
up_time = 1440  # 1d
lw_time = 30    # 50m
up_dist = 100   # ??
lw_dist = 1

# Training Parameters
user_cnt = 32899  # 50 #107092#0
loc_cnt = 1115406  # 50 #1280969#0
reg_lambda = 0.1

# Training Parameters
batch_size = 2
num_epochs = 30
learning_rate = 0.001
momentum = 0.9
evaluate_every = 1
h_0 = Variable(torch.randn(dim, 1), requires_grad=False).type(ftype)

try:
    xrange
except NameError:
    xrange = range


class STRNNCell(nn.Module):

    def __init__(self, hidden_size):
        super(STRNNCell, self).__init__()
        self.hidden_size = hidden_size
        self.weight_ih = nn.Parameter(
            torch.Tensor(hidden_size, hidden_size))  # C
        self.weight_th_upper = nn.Parameter(
            torch.Tensor(hidden_size, hidden_size))  # T
        self.weight_th_lower = nn.Parameter(
            torch.Tensor(hidden_size, hidden_size))  # T
        self.weight_sh_upper = nn.Parameter(
            torch.Tensor(hidden_size, hidden_size))  # S
        self.weight_sh_lower = nn.Parameter(
            torch.Tensor(hidden_size, hidden_size))  # S

        self.location_weight = nn.Embedding(loc_cnt, hidden_size)
        self.permanet_weight = nn.Embedding(user_cnt, hidden_size)

        self.sigmoid = nn.Sigmoid()

        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1.0 / math.sqrt(self.hidden_size)
        for weight in self.parameters():
            weight.data.uniform_(-stdv, stdv)

    def forward(self, td_upper, td_lower, ld_upper, ld_lower, loc, hx):
        loc_len = len(loc)
        Ttd = [((self.weight_th_upper*td_upper[i] + self.weight_th_lower*td_lower[i])
                / (td_upper[i]+td_lower[i])) for i in xrange(loc_len)]
        Sld = [((self.weight_sh_upper*ld_upper[i] + self.weight_sh_lower*ld_lower[i])
                / (ld_upper[i]+ld_lower[i])) for i in xrange(loc_len)]

        loc = self.location_weight(loc).view(-1, self.hidden_size, 1)
#         print("loc:")
#         print(loc)
        loc_vec = torch.sum(torch.cat([torch.mm(Sld[i], torch.mm(Ttd[i], loc[i]))
                                       .view(1, self.hidden_size, 1) for i in xrange(loc_len)], dim=0), dim=0)
#         print("loc_vec:")
#         print(loc_vec)
        usr_vec = torch.mm(self.weight_ih, hx)
#         print("usr_vec:")
#         print(usr_vec)
        hx = loc_vec + usr_vec  # hidden_size x 1
#         print("hx:")
#         print(hx)
        return self.sigmoid(hx)

    def loss(self, user, td_upper, td_lower, ld_upper, ld_lower, loc, dst, hx):
        h_tq = self.forward(td_upper, td_lower, ld_upper, ld_lower, loc, hx)
        p_u = self.permanet_weight(user)
        q_v = self.location_weight(dst)
        output = torch.mm(q_v, (h_tq + torch.t(p_u)))
        # print("output:")
        # print(output)

        return torch.log(1+torch.exp(torch.neg(output)))

    def validation(self, user, td_upper, td_lower, ld_upper, ld_lower, loc, dst, hx):
        # error exist in distance (ld_upper, ld_lower)
        h_tq = self.forward(td_upper, td_lower, ld_upper, ld_lower, loc, hx)
#         print("h_tq:")
#         print(h_tq)
        p_u = self.permanet_weight(user)
#         print("p_u:")
#         print(p_u)
        user_vector = h_tq + torch.t(p_u)
        ret = torch.mm(self.location_weight.weight,
                       user_vector).data.cpu().numpy()
#         print("ret:")
#         print(ret)
        # print("result:")
        # print(len(np.argsort(np.squeeze(-1*ret))))
        # print(np.argsort(np.squeeze(-1*ret)))
        return np.argsort(np.squeeze(-1*ret))
###############################################################################################


def parameters():
    params = []
    for model in [strnn_model]:
        params += list(model.parameters())

    return params


def print_score(batches, step):
    recall1 = 0.
    recall5 = 0.
    recall10 = 0.
    recall100 = 0.
    recall1000 = 0.
    recall10000 = 0.
    iter_cnt = 0

    for batch in batches:#tqdm.tqdm(batches, desc="validation"):
        batch_user, batch_td, batch_ld, batch_loc, batch_dst = batch
        if len(batch_loc) < 3:
            continue
        iter_cnt += 1
        batch_o, target = run(batch_user, batch_td, batch_ld,
                              batch_loc, batch_dst, step=step)
        # print(batch_o)
        return batch_o[:100]
#         print(target)

        recall1 += target in batch_o[:1]
        recall5 += target in batch_o[:5]
        recall10 += target in batch_o[:10]
        recall100 += target in batch_o[:100]
        recall1000 += target in batch_o[:1000]
        recall10000 += target in batch_o[:10000]

    # print("recall@1: ", recall1/iter_cnt, flush=True)
    # print("recall@5: ", recall5/iter_cnt, flush=True)
    # print("recall@10: ", recall10/iter_cnt, flush=True)
    # print("recall@100: ", recall100/iter_cnt, flush=True)
    # print("recall@1000: ", recall1000/iter_cnt, flush=True)
    # print("recall@10000: ", recall10000/iter_cnt, flush=True)
###############################################################################################


def run(user, td, ld, loc, dst, step):

    optimizer.zero_grad()

    seqlen = len(td)
    user = Variable(torch.from_numpy(np.asarray([user]))).type(ltype)

    #neg_loc = Variable(torch.FloatTensor(1).uniform_(0, len(poi2pos)-1).long()).type(ltype)
    #(neg_lati, neg_longi) = poi2pos.get(neg_loc.data.cpu().numpy()[0])
    rnn_output = h_0
    for idx in xrange(seqlen-1):
        td_upper = Variable(torch.from_numpy(
            np.asarray(up_time-td[idx]))).type(ftype)
        td_lower = Variable(torch.from_numpy(
            np.asarray(td[idx]-lw_time))).type(ftype)
        ld_upper = Variable(torch.from_numpy(
            np.asarray(up_dist-ld[idx]))).type(ftype)
        ld_lower = Variable(torch.from_numpy(
            np.asarray(ld[idx]-lw_dist))).type(ftype)
        location = Variable(torch.from_numpy(np.asarray(loc[idx]))).type(ltype)
        # , neg_lati, neg_longi, neg_loc, step)
        rnn_output = strnn_model(
            td_upper, td_lower, ld_upper, ld_lower, location, rnn_output)

    td_upper = Variable(torch.from_numpy(
        np.asarray(up_time-td[-1]))).type(ftype)
    td_lower = Variable(torch.from_numpy(
        np.asarray(td[-1]-lw_time))).type(ftype)
    ld_upper = Variable(torch.from_numpy(
        np.asarray(up_dist-ld[-1]))).type(ftype)
    ld_lower = Variable(torch.from_numpy(
        np.asarray(ld[-1]-lw_dist))).type(ftype)
    location = Variable(torch.from_numpy(np.asarray(loc[-1]))).type(ltype)

    if step > 1:
        return strnn_model.validation(user, td_upper, td_lower, ld_upper, ld_lower, location, dst[-1], rnn_output), dst[-1]

    destination = Variable(torch.from_numpy(np.asarray([dst[-1]]))).type(ltype)
    J = strnn_model.loss(user, td_upper, td_lower, ld_upper, ld_lower, location,
                         destination, rnn_output)  # , neg_lati, neg_longi, neg_loc, step)

    J.backward()
    optimizer.step()

    return J.data.cpu().numpy()

# def save_checkpoint(state, is_best, filename='./checkpoint.pth.tar'):
#     """Save checkpoint if a new best is achieved"""
#     if is_best:
#         # print ("=> Saving a new best", flush=True)
#         torch.save(state, filename)  # save checkpoint
#     # else:
    # print ("=> Validation Accuracy did not improve", flush=True)


id2lalo = pd.read_csv("id2latilongi.csv")
strnn_model = STRNNCell(dim).cuda()
optimizer = torch.optim.SGD(
    parameters(), lr=learning_rate, momentum=momentum, weight_decay=reg_lambda)
strnn_model.load_state_dict(torch.load('./checkpoint.pth.tar')['state_dict'])


def evaluation(train_file="demo.txt"):
    # print("Loading data â€¦")
    train_user, train_td, train_ld, train_loc, train_dst = data_loader.treat_prepro(
        train_file, step=1)
    # strnn_model = STRNNCell(dim).cuda()

#     checkpoint = torch.load('./checkpoint.pth.tar', map_location='cpu')

    train_batches = list(
        zip(train_user, train_td, train_ld, train_loc, train_dst))
#     print(train_batches)
    outputs = print_score(train_batches, 3)
    temp_out = []
    for output in outputs:
        temp_out.append(','.join(str(i) for i in id2lalo.iloc[output]))
    return '\t'.join(str(i) for i in temp_out)


print(evaluation())
