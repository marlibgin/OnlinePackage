#MYSA python conversion
from __future__ import division
#import pkg_resources
#pkg_resources.require('numpy')
#pkg_resources.require('scipy')
#pkg_resources.require('matplotlib')
import numpy
import math
import time
import sys
import os
import random
import scipy.stats as stats

import Tkinter
import ttk
import tkMessageBox

import dls_optimiser_plot as plot
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm
import matplotlib.pyplot as pyplot
from usefulFunctions import *
# colour display codes
ansi_red = "\x1B[31m"
ansi_normal = "\x1B[0m"
#define a global store address so that the program can store the fronts for plotting
#completed_generation is used to keep track of files that store the front infomration
store_address = None
completed_generation = 0

#The following is a list of functions useful to the optimiser bolow
#used to deal with the case of progress handler for the optimiser class
def nothing_function(data):
    pass

def is_dominated(x,y):
    #Takes in two lists of numbers, x and y, to see if x dominates y.
    isLarger = False
    isLargerEqual = True
    for i in range(len(x)):
        if x[i] < y[i]:
            isLarger = True
        if x[i] > y[i]:
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
        x = stats.truncnorm((downBound[i] - params[i])/temp[i],(upBound[i] - params[i])/temp[i], loc = params[i], scale=temp[i]).rvs(size=1)[0]
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
        self.anealPlot = settings_dict['anealPlot']
        self.individuals = individuals
        self.progress_handler = progress_handler
        self.inTemp = []
        self.outTemp = []
        self.domFrontParam = []
        self.domFrontObjectives = []
        self.domFrontErrors = []
        self.inTemp = []
        if progress_handler == None:
            self.progress_handler = nothing_function
        else:
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
        unc = [i.err for i in measure]
        return (f, unc)

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
            testResults.append(objectiveEval[0])
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
            if is_dominated(self.domFrontObjectives[i], newObj[0]):
                notDom = False
            elif is_dominated(newObj[0], self.domFrontObjectives[i]):
                dominatedElements.append(i)
        if notDom:
            self.domFrontObjectives.append(newObj[0])
            self.domFrontErrors.append(newObj[1])
            self.domFrontParam.append(self.param)
            #now to delete the elements use x to keep track of how many are deleted
            x = 0
            for i in dominatedElements:
                del self.domFrontParam[i-x]
                del self.domFrontObjectives[i-x]
                del self.domFrontErrors[i-x]
                x += 1

    def dumpFront(self):
        #at the end in order to plot the fronts we need to save a python file defining the fronts vairalbe which is then used to plot the data.
        f = file("{0}/fronts.{1}".format(self.store_location, completed_generation), "w")
        f.write('fronts = ((\n')
        #we need two ( so that this code is consistent with the DLS plot library.
        for i in range(len(self.domFrontObjectives)):
            f.write('({0}, {1}, {2}), \n'.format(tuple(self.domFrontParam[i][:]),tuple(self.domFrontObjectives[i][:]), tuple(self.domFrontErrors[i][:])))
        f.write('),) \n')
        f.close()

        pass

    def save_details_file(self):
        file_return = ''

        file_return += 'MOSA Algorithm \n'
        file_return += '===================\n\n'
        file_return += 'Number of Aneals: {0}\n'.format(self.nOAneals)
        file_return += 'Number of iterations: {0}\n'.format(self.nOIterations)

        file_return += 'Parameter count: {0}\n'.format(self.paramCount)
        file_return += 'Objective count: {0}\n'.format(self.objCount)
        file_return += 'Output temperture drop: {0}\n'.format(self.passOutTempDrop)
        file_return += 'Minimum parameters: {0}\n'.format(self.down)
        file_return += 'Maximum parameters: {0}\n'.format(self.up)
        file_return += 'Fail drop count: {0}\n'.format(self.failDropCount)
        file_return += 'Maximum number of measurements: {0}\n'.format(self.objCallStop)

        return file_return

    def optimise(self):
        global store_address
        global completed_generation
        store_address = self.store_location
        currentParams = []
        currentObj = ()
        #Two lists above for storing old values whilst new parameters are tested.
        objCall = 0
        #this variable is used to keep track of the number of times we have evaluted the objectives.
        if self.initParam == []:
            self.setUnifRanPoints()
        currentParams = self.param
        currentObj = self.getObjectives()
        #initialise the pareto fronts
        self.domFrontParam.append(currentParams)
        self.domFrontObjectives.append(currentObj[0])
        self.domFrontErrors.append(currentObj[1])
        self.setIinitOutTemp()
        #set the initial input temperture
        self.inTemp = [(self.up[i] - self.down[i])/2 for i in range(self.paramCount)]
        performAneal = True
        aneal = 0
        while performAneal:
            aneal += 1
            pointCount = 0
            failCount = 0
            minObjectives = currentObj[0]
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
                print newObjectives
                #Keep track of how many measurments have been made.
                p = probCalc(newObjectives[0], currentObj[0], self.outTemp)
                #calculate the acceptance probability
                if random.uniform(0,1) < p:
                    currentParams = self.param
                    currentObj = newObjectives
                    pointCount = pointCount + 1
                    self.updateParetoFront(currentObj)
                    #update the minimum objective values
                    minObjectives = min(currentObj[0], minObjectives)
                    failCount = max(math.trunc(failCount/2), 0)
                    #drop the tempertures the tempertures
                    self.inTemp = [self.passInTempDrop[i]*self.inTemp[i] for i in range(self.paramCount)]
                    self.outTemp = [self.passInTempDrop[i]*self.outTemp[i] for i in range(self.objCount)]
                else:
                    failCount = failCount + 1
                    print failCount
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
            k = random.randrange(len(self.domFrontParam))
            currentParams = self.domFrontParam[k]
            currentObj = (self.domFrontObjectives[k], self.domFrontErrors[k])
            if aneal > self.nOAneals:
                performAneal = False
            if objCall > self.objCallStop:
                performAneal = False
            if (aneal % self.anealPlot) == 0:
                #update the front files and let the GUI know of the progress
                completed_generation += 1
                self.dumpFront()
                self.progress_handler(float(aneal)/float(self.nOAneals), aneal)
            while self.pause:
                self.progress_handler(float(aneal)/float(self.nOAneals), aneal)
        self.dumpFront()

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

        Tkinter.Label(self, text='Maximum number of measurements').grid(row=7, column=0, sticky=Tkinter.E)
        self.i7 = Tkinter.Entry(self)
        self.i7.grid(row=7,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Number of aneals between plotting front:').grid(row=8, column=0, sticky=Tkinter.E)
        self.i8 = Tkinter.Entry(self)
        self.i8.grid(row=8, column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text="Recommendations:\nUse as scanning tool when good points not known and then implement GA when the front stops significantly improving\nDo not use if an objective function's best value approaches zero: Ideally the function's 'worst' value should be set to zero \nLength of cycle ~35 if ratios unchanged from default, else refer to doccumentation", justify=Tkinter.LEFT).grid(row=9, column=0, columnspan=2, sticky=Tkinter.W)

        self.i0.insert(0, "3")
        self.i1.insert(0, "2")
        self.i2.insert(0, ':0.9; :0.9; :0.9;')
        self.i3.insert(0, ':0.87; :0.87;')
        self.i4.insert(0, '5')
        self.i5.insert(0, "35")
        self.i6.insert(0, "10")
        self.i7.insert(0, "100000")
        self.i8.insert(0, '1')

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
        setup['initValues'] = []
        setup['anealPlot'] = int(self.i8.get())

        return setup

class import_algo_prog_plot(Tkinter.Frame):

    def __init__(self, parent):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

        self.initUi()

    def initUi(self):

        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.a = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)



    def update(self):
        global store_address
        global completed_generation

        self.a.clear()
        file_names = []
        for i in range(completed_generation):
            file_names.append("{0}/fronts.{1}".format(store_address, i + 1))

        plot.plot_pareto_fronts(file_names, self.a, ["ax1", "ax2"])

        #self.canvas = FigureCanvasTkAgg(self.fig, self.parent)
        self.canvas.show()

class import_algo_final_plot(Tkinter.Frame):

    def __init__(self, parent, pick_handler, axis_labels):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

        self.pick_handler = pick_handler
        self.axis_labels = axis_labels
        #self.initUi()

    def initUi(self):
        global store_address
        global completed_generation

        self.parent.title("MOSA results")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self.rowconfigure(0, weight=1)

        self.view_mode = Tkinter.StringVar()
        self.view_mode.set('No focus')

        self.plot_frame = final_plot(self, self.axis_labels)

        self.plot_frame.grid(row=0, column=0, pady=20, padx=20, rowspan=1, sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)

        Tkinter.Label(self, text="View mode:").grid(row=0, column=1)

        self.cbx_view_mode = ttk.Combobox(self, textvariable=self.view_mode, values=('No focus', 'Best focus'))
        self.cbx_view_mode.bind("<<ComboboxSelected>>", lambda x: self.plot_frame.initUi())
        self.cbx_view_mode.grid(row=0, column=2)

        self.grid(sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

    def on_pick(self, event):

        # Lookup ap values
        my_artist = event.artist
        x_data = my_artist.get_xdata()
        y_data = my_artist.get_ydata()
        ind = event.ind
        point = tuple(zip(x_data[ind], y_data[ind]))

        print "Point selected, point: {0}".format(point)

        ''' By this point we have the ars, but not the aps. We get these next. '''

        file_names = []
        #for i in range(algo_settings_dict['max_gen'])
        for i in range(completed_generation):
            file_names.append("{0}/fronts.{1}".format(store_address, i + 1))


        fs = []

        for file_name in file_names:
            execfile(file_name)

            fs.append(locals()['fronts'][0])

        aggregate_front_data = []
        for i in fs:
            for j in i:
                aggregate_front_data.append(j)
        aggregate_front_results = [i[1] for i in aggregate_front_data]
        point_number = aggregate_front_results.index(point[0])
        point_a_params = aggregate_front_data[point_number][0]

        print "ap: {0}".format(point_a_params)

        ''' By this point he have the aps, but not the mps. We don't find these in the algorithm. '''


        self.pick_handler(point[0], point_a_params)



        #self.pick_handler()





class final_plot(Tkinter.Frame):

    def __init__(self, parent, axis_labels):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.axis_labels = axis_labels

        self.initUi()

    def initUi(self):
        global completed_generation
        global store_address

        for widget in self.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5, 5), dpi=100)
        a = fig.add_subplot(111)
        fig.subplots_adjust(left=0.15)
        #a.plot(range(10), [i**2 for i in range(10)])

        file_names = []
        #for i in range(algo_settings_dict['max_gen']):
        for i in range(completed_generation):
            file_names.append("{0}/fronts.{1}".format(store_address, i + 1))

        plot.plot_pareto_fronts_interactive(file_names, a, self.axis_labels, None, None, self.parent.view_mode.get())

        canvas = FigureCanvasTkAgg(fig, self)
        canvas.mpl_connect('pick_event', self.parent.on_pick)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)
