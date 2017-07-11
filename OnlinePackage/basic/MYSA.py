#MYSA python conversion
from __future__ import division
import numpy
import math
import Tkinter
import time
import sys
import os
import random
import scipy.stats as stats
from matplotlib import pyplot as plt
from usefulFunctions import *
#define a global store address so that the program can store the fronts for plotting
store_address = None

#The following is a list of functions useful to the optimiser bolow

def is_dominated(x,y):
    #Takes in two lists of numbers, x and y, to see if x dominates y.
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
    for i in range(len(newObj)):
        exponent = exponent + (newObj[i] - oldObj[i])/temp[i]
    return min(1, numpy.exp(-exponent))

def addRanGuass(params, temp, upBound, downBound):
    #adds gaussian onto the parameters ensuring that it is stil in bounds
    #this version uses truncated gaussian so as to aviod long loops.
    newPoint = []
    for i in range(len(temp)):
        x = stats.truncnorm((downBound[i] - params[i])/temp[i],(upBound[i] - params[i])/temp[i], loc = params[i], scale=temp[i]).rvs(size=1)
        #generate the truncated normal and then generage the random number to then etract it from the array.
        newPoint.append(x)
    return newPoint

class optimiser:
    def __init__(self, settings_dict, interactor, store_location, a_min_var, a_max_var, individuals=None, progress_handler=None):
        self.interactor = interactor
        self.param = settings_dict['initValues']
        self.initParam = settings_dict['initValues']
        self.up = a_max_var
        self.down = a_min_var
        self.nOIterations = settings_dict['noIterations']
        self.nOAneals = settings_dict['noAneals']
        self.failDropCount = settings_dict['failDropCount']
        self.passOutTempDrop = settings_dict['passOutTempDrop']
        self.passInTempDrop = settings_dict['passInTempDrop']
        self.paramCount = settings_dict['paramCount']
        self.objCount = settings_dict['objCount']
        self.individuals = individuals
        self. progress_handler = progress_handler
        self.inTemp = []
        self.outTemp = []
        self.domFrontParam = []
        self.domFrontObjectives = []
        self.inTemp = []
        self.progress_handler = progress_handler
        self.objCallStop = settings_dict['objCallStop']
        self.store_location = store_location
        self.pause = False
        #pause is used to allow the main GUI to pause the algorithm.

    def getObjectives(self):
        #first we must set the machine to the desired parameter values
        self.interactor.set_ap(self.param)
        #now ask for a measurement
        measure = self.interactor.get_ar()
        #now extract the mean measurment values. The above function returns the measurment as a list of objects that are instances of the
        #the measurment class in dls_optimiser_util
        f = [i.mean for i in measure]
        return f

    def setUnifRanPoints(self):
        #sets the optimisers parameters to somewhere random in their range of allowed values.
        self.param = [random.uniform(self.down[i], self.up[i]) for i in range(self.paramCount)]

    def setIinitOutTemp(self):
        #set the initial output temperture
        numTestPoints = min(2**len(self.up), 16)
        testResults = []
        #essentially preform a test and take some averages of the function values to set the temperture
        for i in range(numTestPoints):
            self.setUnifRanPoints()
            objectiveEval = self.getObjectives()
            testResults.append(objectiveEval)
        for i in range(self.objCount):
            newTemp = mean(extractColumn(testResults, i))
            self.outTemp.append(newTemp)

    def setNewOutTemp(self, objMin):
        #set the new ouput temperture. Used after every aneal
        self.outTemp = [abs(random.gauss(2*objMin[i],4*abs(objMin[i]))) for i in range(self.objCount)]

    def setNewInTemp(self):
        #set the input temperture after an aneal according to the range of allowed values.
        range1 = [(self.up[i] - self.down[i])/2 for i in range(self.paramCount)]
        self.inTemp = [abs(random.gauss(range1[i]/5, range1[i]/2)) for i in range(self.paramCount)]

    def updateParetoFront(self, newObj):
        #loop through the dominated front and see if the new solution can be added and remove
        #any elements dominated by the new solution.
        notDom = True
        dominatedElements = []
        for i in range(len(self.domFrontObjectives)):
            if is_dominated(self.domFrontObjectives[i], newObj):
                notDom = False
            elif is_dominated(newObj, self.domFrontObjectives[i]):
                dominatedElements.append(i)
        if notDom:
            self.domFrontObjectives.append(newObj)
            self.domFrontParam.append(self.param)
            #now to delete the elements use x to keep track of how many are deleted
            x = 0
            for i in dominatedElements:
                del self.domFrontParam[i-x]
                del self.domFrontObjectives[i-x]
                x += 1

    def plotFront(self):
        plt.scatter(extractColumn(self.domFrontObjectives,0), extractColumn(self.domFrontObjectives, 1))
        plt.show()

    def dumpFront(self):
        #at the end in order to plot the fronts we need to save a python file defining the fronts vairalbe which is then used to plot the data.
        f = file('{0}/front'.format(self.store_location), 'w')
        f.write('fronts = ((\n')
        #we need two ( so that this code is consistent with the DLS plot library.
        for obj in self.domFrontObjectives:
            f.write('({0}, 0, 0), /n'.format(obj[:]))
        f.write(')) /n')
        f.close()

    def optimise(self):
        global store_address
        store_address = self.store_location
        currentParams = []
        currentObj = []
        #Two lists above for storing old values whilst new parameters are tested.
        objCall = 0
        #this variable is used to keep track of the number of times we have evaluted the objectives.
        if self.initParam == []:
            self.setUnifRanPoints()
        currentParams = self.param
        currentObj = self.getObjectives()
        #initialise the pareto fronts
        self.domFrontParam.append(currentParams)
        self.domFrontObjectives.append(currentObj)
        self.setIinitOutTemp()
        #set the initial input temperture
        self.inTemp = [(self.up[i] - self.down[i])/2 for i in range(self.paramCount)]
        performAneal = True
        aneal = 0
        while performAneal:
            aneal += 1
            print aneal
            #self.progress_handler(float(aneal)/float(self.nOAneals), 0)
            #while self.pause:
                #self.progress_handler(float(aneal)/float(self.nOAneals), 0)
            pointCount = 0
            failCount = 0
            minObjectives = currentObj
            keepIterating = True
            x = 0
            #initialise the current minimum objectives. This variable will be used to keep track of the minimum objectives so as to help in calculating the new output temperture.
            while keepIterating:
                x = x + 1
                self.param = addRanGuass(currentParams, self.inTemp, self.up, self.down)
                #generate a new parameter set
                newObjectives = self.getObjectives()
                #and measure the objective values
                objCall = objCall + 1
                #Keep track of how many measurments have been made.
                p = probCalc(newObjectives, currentObj, self.outTemp)
                #calculate the acceptance probability
                if random.uniform(0,1) < p:
                    currentParams = self.param
                    currentObj = newObjectives
                    pointCount = pointCount + 1
                    self.updateParetoFront(currentObj)
                    #update the minimum objective values
                    minObjectives = min(currentObj, minObjectives)
                    failCount = max(math.trunc(failCount/2), 0)
                    #drop the tempertures the tempertures
                    self.inTemp = [self.passInTempDrop[i]*self.inTemp[i] for i in range(self.paramCount)]
                    self.outTemp = [self.passInTempDrop[i]*self.outTemp[i] for i in range(self.objCount)]
                else:
                    failCount = failCount + 1
                    #reduce input temperture slightly
                    self.inTemp = [0.95**(max(self.failDropCount, failCount) - self.failDropCount)*self.inTemp[i] for i in range(self.paramCount)]
                #check to see if enough ponits have been checked and if so leave this loop
                if pointCount == self.nOIterations:
                    keepIterating = False
                elif x == (self.nOIterations*100):
                    print 'failed to complete in 100*(number of iterations) check code'
                    keepIterating = False
            #set the new tempertures for a new anneal
            self.setNewInTemp()
            self.setNewOutTemp(minObjectives)
            #now set new starting point from the pareto front
            x = random.randrange(len(self.domFrontParam))
            currentParams = self.domFrontParam[x]
            currentObj = self.domFrontObjectives[x]
            if aneal > self.nOAneals:
                performAneal = False
            if objCall > self.objCallStop:
                performAneal = False
        self.plotFront()

class import_algo_frame(Tkinter.Frame):
    #this class deals with the GUI for the algorithm. The main GUI will call this to get algorithm settings and so is called before optimise.
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.initUi()

    def initUi(self):
        #this generates a number of widgets in the algorithm frame to input the settings with.
        Tkinter.Label(self, text='Parameter count:').grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self)
        self.i0.grid(row=0,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Objective count:').grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self)
        self.i1.grid(row=1, column=1, sticky = Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Input temperture drops:').grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self)
        self.i2.grid(row=2,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Objectives temperture drops:').grid(row=3, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self)
        self.i3.grid(row=3,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Number of aneals:').grid(row=4, column=0, sticky=Tkinter.E)
        self.i4 = Tkinter.Entry(self)
        self.i4.grid(row=4,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Number of iterations:').grid(row=5, column=0, sticky=Tkinter.E)
        self.i5 = Tkinter.Entry(self)
        self.i5.grid(row=5,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Fail drop count').grid(row=6, column=0, sticky=Tkinter.E)
        self.i6 = Tkinter.Entry(self)
        self.i6.grid(row=6,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Objective call stop').grid(row=7, column=0, sticky=Tkinter.E)
        self.i7 = Tkinter.Entry(self)
        self.i7.grid(row=7,column=1, sticky=Tkinter.E + Tkinter.W)


    def get_dict(self):
        #extracts the inputted settings to put in settings dictionary
        setup = {}

        setup['paramCount'] = int(self.i0.get())
        setup['objCount'] = int(self.i1.get())
        setup['passInTempDrop'] = extractNumbers(self.i2.get())
        setup['passOutTempDrop'] = extractNumbers(self.i3.get())
        setup['noAneals'] = int(self.i4.get())
        setup['noIterations'] = int(self.i5.get())
        setup['failDropCount'] = int(self.i6.get())
        setup['objCallStop'] = int(self.i7.get())

        return setup

class final_plot(Tkinter.Frame):
    def __init__(self):
        Tkinter.Frame.__init__(self, parent, axis_labels)

        self.parent = parent
        self.axis_labels = axis_labels

        self.initUi()

    def initUi():
        for widget in self.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5, 5), dpi=100)
        a = fig.add_subplot(111)
        fig.subplots_adjust(left=0.15)

        file_names = []
        #for i in range(algo_settings_dict['max_gen']):
        file_names.append("{0}/fronts".format(store_address))

        plot.plot_pareto_fronts_interactive(file_names, a, self.axis_labels, None, None, self.parent.view_mode.get())

        canvas = FigureCanvasTkAgg(fig, self)
        canvas.mpl_connect('pick_event', self.parent.on_pick)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)
