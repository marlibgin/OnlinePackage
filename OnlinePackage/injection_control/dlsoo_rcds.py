#RCDS optimiser
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
import scipy
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
# colour display codes
ansi_red = "\x1B[31m"
ansi_normal = "\x1B[0m"
#define a global store address so that the program can store the fronts for plotting
#completed_generation is used to keep track of files that store the front infomration
store_address = None
completed_generation = 1
goldenRatio = 1.618034
userInputDirections = []

def nothing_function(x,y):
    pass

def unNormalise(x, down, up):
    x1 = [down[i] + x[i]*(up[i] - down[i]) for i in range(len(x))]
    return x1

def vecNormalise(x):
    #normalise a column vector x
    vecNorm = sum([i^2 for i in x])**0.5
    x = [i/vecNorm for i in x]

def removeOutliers(differenceList):
    mul_tol = 3
    perlim = 0.25
    y = sorted(differenceList)
    dy = [y[i+1] - y[i] for i in range(len(differenceList) - 1)]
    upl = max(int((1-perlim)*len(y)), 3)
    dnl = max(int(perlim*len(y)), 2)
    stddy = sum(dy[(dnl-1):(upl)])/(upl - dnl)
    upcut = len
    dncut = -1
    for i in range(upl - 1, len(y) - 1):
        if dy[i] > mul_tol*stddy:
            upcut = i + 1
    for i in range(dnl + 1):
        if dy[dnl - i] > mul_tol:
            dncut = dnl - i
    lower = [differenceList.index(y[i]) for i in range(len(y)) if i <= dncut]
    upper = [differenceList.index(y[i]) for i in range(len(y)) if i >= upcut]
    return (lower + upper)




class optimiser:
    def __init__(self, settings_dict, interactor, store_location, a_min_var, a_max_var, individuals=None, progress_handler=None):
        self.interactor = interactor
        self.searchDirections = settings_dict['searchDirections']
        self.paramCount = len(interactor.param_var_groups)
        self.initStep = settings_dict['initStep']
        self.objCallStop = settings_dict['objCallStop']
        self.tolerance = settings_dict['tolerance']
        self.nOIterations = settings_dict['nOIterations']
        self.numTestPoints = settings_dict['numTestPoints']
        self.down = a_min_var
        self.up = a_max_var
        if not type(self.up) == type([]):
            self.up = [self.up]
            self.down = [self.down]
        if progress_handler == None:
            self.progress_handler = nothing_function
        else:
            self.progress_handler = progress_handler
        self.progressTracker = []
        self.store_location = store_location
        if self.searchDirections == []:
            for i in range(self.paramCount):
                searchDirection = []
                for j in range(self.paramCount):
                    if j == i:
                        searchDirection.append(1)
                    else:
                        searchDirection.append(0)
                self.searchDirections.append(searchDirection)
        self.numFuncEval = 0
        self.numDirSearched = 0
        self.pause = False
        self.cancel = False
        #if now perameters specified use random
        if settings_dict['add_current_to_individuals']:
            self.initParams = interactor.get_ap()
        else:
            self.initParams = [random.uniform(self.down[i], self.up[i]) for i in range(self.paramCount)]

    def getParams(self):
        params = [self.down[i] + self.normParam[i]*(self.up[i] - self.down[i]) for i in range(self.paramCount)]
        return params

    def getObjective(self):
        params = self.getParams()
        #first we must set the machine to the desired parameter values
        self.interactor.set_ap(params)
        #now ask for a measurement
        measure = self.interactor.get_ar()
        self.numFuncEval += 1
        #now extract the mean measurment values. The above function returns the measurment as a list of objects that are instances of the
        #the measurment class in dls_optimiser_util
        f = measure[0].mean
        unc = measure[0].err
        return (f, unc)

    def bracketMin(self, initialVec, searchDirection):
        global goldenRatio
        vecFuncStore = []
        self.normParam = initialVec
        initFunc = self.getObjective()
        vecFuncStore.append([initialVec, initFunc, 0])
        g_noise = initFunc[1]
        funcMin = initFunc
        vecMin = initialVec
        alphaMin = 0
        step = self.initStep

        self.normParam = [initialVec[i] + step*searchDirection[i] for i in range(self.paramCount)]
        if any([not (0 <= i <= 1) for i in self.normParam]):
            funcTest = initFunc
            step = 0
        else:
            funcTest = self.getObjective()
            vecFuncStore.append([self.normParam, funcTest, step])
        if funcTest[0] < funcMin[0]:
            funcMin = funcTest
            alphaMin = step
            vecMin = self.normParam

        while funcTest[0] < (funcMin[0] + 3*g_noise):
            step = step*(1 + goldenRatio)
            self.normParam = [initialVec[i] + step*searchDirection[i] for i in range(self.paramCount)]
            if any([not (0 <= i <= 1) for i in self.normParam]) or (step == 0):
                step = step/(1 + goldenRatio)
                break
            else:
                funcTest = self.getObjective()
                vecFuncStore.append([self.normParam, funcTest, step])
            if funcTest[0] < funcMin[0]:
                funcMin = funcTest
                vecMin = self.normParam
                alphaMin = step

        alpha2 = step
        if initFunc[0] > (funcMin[0] + 3*g_noise):
            alpha1 = 0
            alpha1 = alpha1 - alphaMin
            alpha2 = alpha2 - alphaMin
            for i in range(len(vecFuncStore)):
                vecFuncStore[i][2] = vecFuncStore[i][2] - alphaMin
            return (vecMin, funcMin, alpha1, alpha2, vecFuncStore)
        print self.initStep
        step = -self.initStep

        self.normParam = [initialVec[i] + step*searchDirection[i] for i in range(self.paramCount)]
        if any([not (0 <= i <= 1) for i in self.normParam]):
            funcTest = initFunc
            step = 0
        else:
            funcTest = self.getObjective()
            vecFuncStore.append([self.normParam, funcTest, step])
        if funcTest[0] < funcMin[0]:
            funcMin = funcTest
            alphaMin = step
            vecMin = self.normParam

        while funcTest[0] < (funcMin[0] + 3*g_noise):
            step = step*(1 + goldenRatio)
            self.normParam = [initialVec[i] + step*searchDirection[i] for i in range(self.paramCount)]
            if any([not (0 <= i <= 1) for i in self.normParam]) or (step == 0):
                step = step/(1 + goldenRatio)
                break
            else:
                funcTest = self.getObjective()
                vecFuncStore.append([self.normParam, funcTest, step])
            if funcTest[0] < funcMin[0]:
                funcMin = funcTest
                vecMin = self.normParam
                alphaMin = step

        alpha1 = step

        if alpha1 > alpha2:
            alpha1, alpha2 = (alpha2, alpha1)
        alpha1 = alpha1 - alphaMin
        alpha2 = alpha2 - alphaMin
        for i in range(len(vecFuncStore)):
            vecFuncStore[i][2] = vecFuncStore[i][2] - alphaMin
        return (vecMin, funcMin, alpha1, alpha2, vecFuncStore)

    def findMinimum(self, alpha1, alpha2, searchDirection, initialVec, initFunc, vecFuncStore):
        #perform a line search
        delta = (alpha2 - alpha1)/(self.numTestPoints - 1)
        if delta == 0:
            return (initialVec, initFunc, 0)
        alphaTestList = (alpha1 + delta*i for i in range(self.numTestPoints))
        #only use previous points that are in range
        vecFunc0List = [i for i in vecFuncStore if (alpha1 <= i[2] <= alpha2)]
        vecFunc0List = sorted(vecFunc0List, key = lambda i: i[2])
        #now only have test points that are suffciently far away from the already known points
        alphaTestList = [i for i in alphaTestList if min([abs(i - j[2]) for j in vecFunc0List]) > delta/2]
        #now evaluate all the new test points
        vecFuncTest = []
        for alpha in alphaTestList:
            self.normParam = [initialVec[i] + alpha*searchDirection[i] for i in range(self.paramCount)]
            funcTest = self.getObjective()
            vecFuncTest.append([self.normParam, funcTest, alpha])
        #now combine all points into one list
        vecFuncList = vecFuncTest + vecFunc0List
        #and sort the list according to the value of alpha
        vecFuncList = sorted(vecFuncList, key = lambda i: i[2])
        #now fit a parabola to the data
        x = [i[2] for i in vecFuncList]
        y = [i[1][0] for i in vecFuncList]
        pyplot.plot(x,y, '.')
        pyplot.xlabel('Distance along search direction (in normalised parameter space)')
        pyplot.ylabel('Objective function')
        p = list(numpy.polyfit(numpy.array(x), numpy.array(y), 2))
        print 'p'
        print p
        fittedValues = [p[0]*(x[i]**2) + p[1]*x[i] + p[2] for i in range(len(x))]
        pyplot.plot(x,fittedValues)
        #pyplot.show()
        #differenceList is used to get rid of outliers
        differenceList = [fittedValues[i] - y[i] for i in range(len(y))]
        removeIndex = removeOutliers(differenceList)
        #removeIndex is a list of the index of all points that are considered outliers
        if len(removeIndex) <= 1:
            if len(removeIndex) == 1:
                del y[removeIndex[0]]
                del x[removeIndex[0]]
                p = list(numpy.polyfit(numpy.array(x), numpy.array(y), 2))
            alphaMin = -p[1]/(2*p[0])
            if p[0] < 0:
                alpha1Predict = p[0]*alpha1**2 + p[1]*alpha1 + p[2]
                alpha2Predict = p[0]*alpha2**2 + p[1]*alpha2 + p[2]
                if alpha2Predict < alpha1Predict:
                    return [vecFuncList[-1][0], (alpha2Predict, vecFuncList[-1][1][1]), alpha2]
                else:
                    return [vecFuncList[0][0], (alpha1Predict, vecFuncList[0][1][1]), alpha1]
            else:
                if alphaMin < alpha1:
                    print vecFuncList[0]
                    print '======0'
                    print min(vecFuncList, key = lambda i: i[1][0])
                    alpha1Predict = p[0]*alpha1**2 + p[1]*alpha1 + p[2]
                    return [vecFuncList[0][0], (alpha1Predict, vecFuncList[0][1][1]), alpha1]
                elif alphaMin > alpha2:
                    print vecFuncList[-1]
                    print '=========1'
                    print min(vecFuncList, key = lambda i: i[1][0])
                    alpha2Predict = p[0]*alpha2**2 + p[1]*alpha2 + p[2]
                    return [vecFuncList[-1][0], (alpha2Predict, vecFuncList[-1][1][1]), alpha2]
                else:
                    self.normParam = [initialVec[i] + alphaMin*searchDirection[i] for i in range(self.paramCount)]
                    returner = [self.normParam, self.getObjective(), alphaMin]
                    print alphaMin
                    print returner
                    print '=============2'
                    print min(vecFuncList, key = lambda i: i[1][0])
                    return returner
        else:
            return min(vecFuncList, key = lambda i: i[1][0])

    def dumpProgress(self):
        #at the end in order to plot the fronts we need to save a python file defining the fronts vairalbe which is then used to plot the data.
        f = file("{0}/fronts.{1}".format(self.store_location, completed_generation), "w")
        f.write('fronts = ((\n')
        #we need two ( so that this code is consistent with the DLS plot library.
        for i in self.progressTracker:
            f.write('{0}, \n'.format(i))
        f.write('),) \n')
        f.close()

        pass

    def save_details_file(self):
        #when the optimsation is finished this is called in order to save the settings of the algorithm.
        file_return = ''

        file_return += 'dlsoo_rcds.py algorithm\n'
        file_return += '===================\n\n'
        file_return += 'Number of iterations: {0}\n'.format(self.nOIterations)

        file_return += 'Parameter count: {0}\n'.format(self.paramCount)
        file_return += 'Minimum parameters: {0}\n'.format(self.down)
        file_return += 'Maximum parameters: {0}\n'.format(self.up)
        file_return += 'Maximum number of measurements: {0}\n'.format(self.objCallStop)
        file_return += 'Finishing tolerance: {0}\n'.format(self.tolerance)
        return file_return

    def optimise(self):
        global store_address
        print self.searchDirections
        store_address = self.store_location
        maxDirSearches = self.nOIterations*self.paramCount
        #first set the inital values
        x0 = [(self.initParams[i] - self.down[i])/(self.up[i] - self.down[i]) for i in range(self.paramCount)]
        self.normParam = x0
        initFunc = self.getObjective()
        vecMin = x0
        funcMin = initFunc
        #x0 and initFunc will keep track of the inital parameters and objective at the start of each iteration.
        #now begin the iterations
        for i in range(self.nOIterations):
            self.initStep = self.initStep/1.2
            dirToDelete = 0
            del1 = 0
            #del1 keeps track of the largest change so far in the iteration.
            for j in range(self.paramCount):
                #begin searching along each direction
                searchDirection = self.searchDirections[j]
                x1, f1, a1, a2, xflist = self.bracketMin(vecMin, searchDirection)
                print a1
                print a2
                x1, f1, alpha = self.findMinimum(a1, a2, searchDirection, x1, f1, xflist)
                if (funcMin[0] - f1[0]) > del1:
                    del1 = funcMin[0] - f1[0]
                    dirToDelete = j
                funcMin = f1
                vecMin = x1
                self.numDirSearched += 1
                self.progressTracker.append((tuple(unNormalise(vecMin, self.down, self.up)), (self.numDirSearched, funcMin[0]), (0, funcMin[1])))
                self.dumpProgress()
                self.progress_handler(float(self.numDirSearched)/float(maxDirSearches), self.numDirSearched)
            newDirection = [vecMin[k] - x0[k] for k in range(self.paramCount)]
            norm = sum([k**2 for k in newDirection])**0.5
            print self.searchDirections
            print 'searchDirections'
            if not (norm == 0):
                newDirection = [k/norm for k in newDirection]
                dotProduct = []
                for k in self.searchDirections:
                    dot = abs(sum([newDirection[l]*k[l] for l in range(self.paramCount)]))
                    dotProduct.append(dot)
                if max(dotProduct) <= 0.9:
                    del self.searchDirections[dirToDelete]
                    self.searchDirections.append(newDirection)
            if self.numFuncEval >= self.objCallStop:
                print 'Exceeded max number of measurements'
            if 2*abs(initFunc[0] - funcMin[0]) < self.tolerance*(abs(initFunc[0]) + abs(funcMin[0])):
                print 'Finished'
                break
            x0 = vecMin
            initFunc = funcMin

class import_algo_frame(Tkinter.Frame):
    #this class deals with the GUI for the algorithm. The main GUI will call this to get algorithm settings and so is called before optimise.
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)
        self.parent = parent
        self.initUi()

    def initUi(self):
        #this generates a number of widgets in the algorithm frame to input the settings with.
        self.add_current_to_individuals = Tkinter.BooleanVar(self)
        self.add_current_to_individuals.set(True)

        Tkinter.Label(self, text='Number of iterations:').grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self)
        self.i2.grid(row=2,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Finishing tolerance:').grid(row=3, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self)
        self.i3.grid(row=3,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Maximum number of measurements:').grid(row=4, column=0, sticky=Tkinter.E)
        self.i4 = Tkinter.Entry(self)
        self.i4.grid(row=4,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Line search initial step (in normalised peramter space):').grid(row=5, column=0, sticky=Tkinter.E)
        self.i5 = Tkinter.Entry(self)
        self.i5.grid(row=5,column=1, sticky=Tkinter.E + Tkinter.W)

        Tkinter.Label(self, text='Number of test points in line search:').grid(row=6, column=0, sticky=Tkinter.E)
        self.i6 = Tkinter.Entry(self)
        self.i6.grid(row=6,column=1, sticky=Tkinter.E + Tkinter.W)

        self.c0 = Tkinter.Checkbutton(self, text='Use current machine state', variable=self.add_current_to_individuals)
        self.c0.grid(row=9,column=0)

        Tkinter.Label(self, text="Recommendations:\n Consult doccumentation for the MATLAB version of RCDS.", justify=Tkinter.LEFT).grid(row=10, column=0, columnspan=2, sticky=Tkinter.W)

        self.i2.insert(0, '10')
        self.i3.insert(0, '0.01')
        self.i4.insert(0, '500')
        self.i5.insert(0, "0.05")
        self.i6.insert(0, '10')

    def get_dict(self):
        #extracts the inputted settings to put in settings dictionary
        setup = {}

        setup['nOIterations'] = int(self.i2.get())
        setup['tolerance'] = float(self.i3.get())
        setup['objCallStop'] = int(self.i4.get())
        setup['initStep'] = float(self.i5.get())
        setup['numTestPoints'] = int(self.i6.get())
        setup['searchDirections'] = []
        if self.add_current_to_individuals.get() == 0:
            setup['add_current_to_individuals'] = False
        elif self.add_current_to_individuals.get() == 1:
            setup['add_current_to_individuals'] = True


        return setup

class import_algo_prog_plot(Tkinter.Frame):

    def __init__(self, parent, axis_labels, signConverter):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.signConverter = [1, signConverter[0]]
        self.axis_labels = ['Number of searched directions', axis_labels[0]]

        self.initUi()

    def initUi(self):

        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.a = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)



    def update(self):
        global store_address
        global completed_iteration
        self.a.clear()
        file_names = []
        for i in range(completed_generation):
            file_names.append("{0}/fronts.{1}".format(store_address, i + 1))

        plot.plot_pareto_fronts(file_names, self.a, self.axis_labels, self.signConverter)

        #self.canvas = FigureCanvasTkAgg(self.fig, self.parent)
        self.canvas.show()

class import_algo_final_plot(Tkinter.Frame):

    def __init__(self, parent, pick_handler, axis_labels, signConverter):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.signConverter = [1 , signConverter[0]]

        self.pick_handler = pick_handler
        self.axis_labels = ['Number of directions searched', axis_labels[0]]
        #self.initUi()

    def initUi(self):
        global store_address

        self.parent.title("MOPSO results")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self.rowconfigure(0, weight=1)

        self.view_mode = Tkinter.StringVar()
        self.view_mode.set('No focus')

        self.plot_frame = final_plot(self, self.axis_labels, self.signConverter)

        self.plot_frame.grid(row=0, column=0, pady=20, padx=20, rowspan=1, sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)

        Tkinter.Label(self, text="View mode:").grid(row=0, column=1)

        self.cbx_view_mode = ttk.Combobox(self, textvariable=self.view_mode, values=('No focus', 'Best focus'))
        self.cbx_view_mode.bind("<<ComboboxSelected>>", lambda x: self.plot_frame.initUi())
        self.cbx_view_mode.grid(row=0, column=2)

        self.grid(sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

    def on_pick(self, event):
        global completed_generation
        # Lookup ap values
        my_artist = event.artist
        x_data = my_artist.get_xdata()
        y_data = my_artist.get_ydata()
        ind = event.ind
        point = tuple(zip(self.signConverter[0]*x_data[ind], self.signConverter[1]*y_data[ind]))

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

    def __init__(self, parent, axis_labels, signConverter):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.signConverter = signConverter
        self.axis_labels = axis_labels

        self.initUi()

    def initUi(self):
        global store_address
        global completed_generation

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

        plot.plot_pareto_fronts_interactive(file_names, a, self.axis_labels, None, None, self.parent.view_mode.get(), self.signConverter)

        canvas = FigureCanvasTkAgg(fig, self)
        canvas.mpl_connect('pick_event', self.parent.on_pick)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)