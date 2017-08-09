#Some helpful functions for MYSA

from __future__ import division
import csv

def extractColumn(matrix, colnum):
    col = []
    for i in matrix:
        col.append(i[colnum])
    return col

def mean(x):
    return sum(x)/len(x)

def extractNumbers(string1):
    #takes in a list and extracts the numbers with : ; around them to then stor in a list.
    collect = False
    collector = ''
    numbers = []
    for i in string1:
        if i == ':':
            collect = True
        elif i == ';':
            collect = False
            numbers.append(float(collector))
            collector = ''
        elif collect:
            collector += i
    return numbers

def frontReader(fileName):
    '''
    Takes in the csv file containing the front information and reads and returns a tuple with the first entry is the list of the parameters and the second is a list of the objectives for each point on the front.
    '''
    f = open(fileName, 'r')
    wr = csv.reader(f)
    params = []
    objectives = []
    for row in wr:
        params.append(row[:3])
        objectives.append(row[3:])
    f.close()
    params = [[float(j) for j in i] for i in params]
    objectives = [[float(j) for j in i] for i in objectives]

    return (params, objectives)
