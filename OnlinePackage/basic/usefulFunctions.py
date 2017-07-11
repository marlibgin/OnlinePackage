#Some helpful functions for MYSA

from __future__ import division

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
