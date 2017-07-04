#MYSA python conversion
import numpy
import matplotlib
import Tkinter
import time
import sys
import os
import statistics
from usefulFunctions import *

#The following is a list of functions useful to the optiser bolow

def is_dominated(x,y):
    """Takes in two lists of numbers, x and y, to see if x dominates y."""
    isLarger = False
    isLargerEqual = True
    for i in range(len(x)):
        if x[i] > y[i]:
            isLarger = True
        if x[i] < y[i]:
            isLargerEqual = False
    return (isLargerEqual and isLarger)

def probCalc(newObj, oldObj, temp):
    #calculate the acceptance probability for a new set of parameters
    exponent = 0
    for i in range(len(obj)):
        exponent = exponent + (newObj[i] - oldObj[i])/temp[i]
    return min(1, numpy.exp(exponent))

def addRanGuass(params, temp, upBound, downBound):
    #adds gaussian onto the paramets ensuring that it is stil in bounds
    outOfBounds = True
    holder = x
    while outOfBounds:
        x = holder
        for i in range(len(params)):
            x[i] = x[i] + random.gauss(0, temp[i])
        if (x <= upBound) and (x >= downBound):
            outOfBounds = False
    return x


class MYSA_optimiser:
    def __init__(self, interactor, initValues = [], upbound, downbound, noIterations, noAneals, failDropout, passOutTempDrop, passInTempDrop, paramCount, objCount):
        self.interactor = interactor
        self.param = initValues
        self.initParam = initValues
        self.up = upbound
        self.down = downbound
        self.nOIterations = noIterations
        self.nOAneals = noAneals
        self.failDropout = failDropout
        self.passOutTempDrop = passOutTempDrop
        self.passInTempDrop = passInTempDrop
        self.paramCount = paramCount
        self.objCount = objCount
        self.inTemp = []
        self.outTemp = []
        self.domFrontParam = [[]]
        self.domFrontObjectives = [[]]
        self.inTemp = []

        #set the initial input temperture
        for i in range(paramCount):
            temp = (upbound[i] - downbound[i])/2
            self.inTemp.append(temp)

        if len(initValues) == 0:
            self.setUnifRanPoints()


    def getObjectives(self):
        #soon to contain the method for evaluating the objectives

    def setUnifRanPoints(self):
        for i in range(self.paramCount:
            self.param[i] = random.uniform(down[i], up[i])

    def setIinitOutTemp(self);
        numTestPoints = min(2**len(upbound), 16)
        testResults = [[]]
        for i in range(len(numTestPoints)):
            self.setUnifRanPoints()
            objectiveEval = self.getObjectives()
            results.append(objectiveEval)
        for i in range(self.objCount):
            newTemp = statistics.mean(extractColumn(results, i))
            self.outTemp.append(newTemp)
