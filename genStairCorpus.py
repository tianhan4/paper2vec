#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author : HenrySky
# Date : 2016/1/17
# Function : transform from paper adjalist data to start training corpus.
# Parameter :   window size win
#               adjalist file fin
#               output corpus file fout

import os
import sys
import numpy as np
import argparse
import scipy.sparse
import random
from math import log
decayRate = 0

#Algorithm : http://stackoverflow.com/questions/2140787/select-k-random-elements-from-a-list-whose-elements-have-weights
def weighted_sample(dic, n):
    if len(dic) == 0:
        return -1
    total = sum(dic.values())
    items = sorted(dic.items(), key=lambda d: d[1], reverse=True)
    i = 0
    v, w = items[0]
    while n:
        x = total * (1 - random.random() ** (1.0/n))
        total -= x
        while x > w:
            x -= w
            i += 1
            v, w = items[i]
        w -= x
        yield v
        n -= 1
        

def extractData(filename):
    lookupDict = {}
    idxList = []
    citingList = []
    citedList = []
    countList = []
    with open(filename, "r") as f:
        index = 0
        while True:
            line = f.readline()
            if not line:
                break
            docs = line.strip().split()
            if len(docs) > 1:
                print("Corrupted data. {} error >1.".format(index))
            if docs[0] in lookupDict.keys():
                print("Corrupted data. {} line error existed.".format(index))
            lookupDict[docs[0]] = index
            idxList.append(docs[0])
            f.readline()
            f.readline()
            index += 1
    with open(filename, "r") as f:
        index = 0
        while True:
            line = f.readline()
            if not line:
                break
            citingLine = [lookupDict[z] for z in f.readline().strip().split()]
            citedLine = [lookupDict[z] for z in f.readline().strip().split()]
            citedList.append(citedLine)
            citingList.append(citingLine)
            countList.append(len(citingLine)+len(citedLine))
            index += 1
    return idxList, citedList, citingList, countList

def outputStairData(idxList, citedList, citingList, countList, fout, win, iterate):
    #print(lookupDic, adjaList)
    global decayRate
    consideredDocs = set()
    learningWeights = np.zeros((len(countList)), dtype=int)
    contextWeights = []
#    iterList = [iterate * 3, int(iterate * 2.5), int(iterate * 2)]
    oneProbability = np.ones((len(countList)), dtype=float)
    for i in range(len(idxList)):
        contextWeights.append({i: 1})
    with open(fout, "w") as f:
        for i in range(len(idxList)):
            if i % 100 == 0:
                print("\r%%%.2f"%(100.0*i/len(idxList)), end="")
            #distant = np.zeros(len(idxList))
            # drop later
            buildSet = {i}
            froutiers = {i}
            for w in range(win):
                newFrontier = set()
                for froutier in froutiers:
                    if contextWeights[i][froutier]/(countList[froutier]+1) < 1e-6:
                        continue
                    for k in citingList[froutier]:
                        if k in contextWeights[i].keys():
                            # it doesn't matter if first window is decayed, for the relative not the absolute value is considered.
                            contextWeights[i][k] += decayRate * contextWeights[i][
                                froutier]/countList[froutier]
#                           contextWeights[i][k] += contextWeights[i][froutier] * decayRate
                        else:
                            #distant[k] = w + 1
                            contextWeights[i][k] = decayRate * contextWeights[i][
                                froutier]/countList[froutier]
#                           contextWeights[i][k] = contextWeights[i][froutier] * decayRate
                    for k in citedList[froutier]:
                        if k in contextWeights[i].keys():
                            contextWeights[i][k] += decayRate * contextWeights[i][
                                froutier]/countList[froutier]
#                           contextWeights[i][k] += contextWeights[i][froutier] * decayRate
                        else:
                            #distant[k] = w + 1
                            contextWeights[i][k] = decayRate * contextWeights[i][
                                froutier]/countList[froutier]
#                           contextWeights[i][k] = contextWeights[i][froutier] * decayRate
                    newFrontier = newFrontier.union(citedList[froutier])
                    newFrontier = newFrontier.union(citingList[froutier])

                # print("newFroutier : ", newFrontier)
                froutiers = newFrontier.difference(buildSet)
                if len(froutiers) == 0:
                    continue
                buildSet = buildSet.union(froutiers)

#            consideredDocs.add(i)
            for idx in weighted_sample(contextWeights[i], iterate):
                f.write(idxList[i] #+ " " + str(countList[con])
#                           + " " + str(1)
                        + " " + idxList[idx] + "\n")
            '''
            for con in buildSet:
                if con == i:
                    pass
                    
                    f.write(idxList[i] + " " + str(countList[con])
                            + " " + str(1)
                            + " " + idxList[con] + "\n")
                else:
                    temp = contextWeights[i].pop(con)
                    for j in range(temp):
                        f.write(idxList[i] #+ " " + str(countList[con])
                            #+ " " + str(tempi)
                            + " " + idxList[con] + "\n")

                '''
def process(win, fin, fout, iterate):
    print("Extract adjalist...");
    idxList, citedList, citingList, countList = extractData(fin)
    print("Output corpus...");
    outputStairData(idxList, citedList, citingList, countList, fout, win, iterate)

def parseArg():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="the step window of citation linkage context.",
                        type=int, default=3)
    parser.add_argument("-fin", "--input", help="Input adjalist filename.",
                        required=True)
    parser.add_argument("-fout", "--output", help="Output corpus filename.",
                        required=True)
    parser.add_argument("-decay", "--decay", help="Decay factor for further nodes.", type=float,
                        default=1.0)
    parser.add_argument("-iter", "--iterate", help="times starting from each node.", type=int, default=200)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parseArg()
    decayRate = args.decay
    process(args.window, args.input, args.output, args.iterate)
