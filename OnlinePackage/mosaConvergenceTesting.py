'''
MOSA Convergence Testing
@authors: Greg Henderson
'''

import numpy
import csv
import matplotlib
import matplotlib.pyplot as plot
import fastTestingClasses
import dlsoo_mosa
import metrics
from usefulFunctions import frontReader

#initialise the test enviroment
interactor = fastTestingClasses.interactorFast('kur')
settings_dict_short = {'noIterations': 25, 'passInTempDrop': 3*[0.9], 'passOutTempDrop': 2*[0.87], 'failDropCount': 1, 'anealPlot': 10000000000, 'add_current_to_individuals': True, 'dumpFlag': False}
annealNums = range(2, 82, 2)
metricData = [[i] for i in range(6)]
a_min_var = 3*[-4]
a_max_var = 3*[4]

acturalFrontParams, actualFrontObjectives = frontReader('kurFront.csv')

#Now do the convergence test
for i in annealNums:
    settings_dict_short['noAneals'] = i
    settings_dict_short['objCallStop'] = i*25
    m = 6*[0]
    for j in range(5):
        optimiser = dlsoo_mosa.optimiser(settings_dict = settings_dict_short, interactor = interactor, store_location = '', a_min_var = a_min_var, a_max_var = a_max_var)
        optimiser.optimise()
        m[0] += metrics.metric1(acturalFrontParams, optimiser.domFrontParam)
        m[1] += metrics.metric2(optimiser.domFrontParam, 0.5)
        m[2] += metrics.metric3(optimiser.domFrontParam)
        m[3] += metrics.metric1(actualFrontObjectives, optimiser.domFrontObjectives)
        m[4] += metrics.metric2(optimiser.domFrontObjectives, 0.5)
        m[5] += metrics.metric3(optimiser.domFrontObjectives)
    m = [float(l)/5 for l in m]
    for j in range(6):
        metricData[j].append(m[j])
    print 'Done: {0}'.format(i)

#File saving
f = open('mosaConvergenceData.csv', 'w')
wr = csv.writer(f)
x = [i*25 for i in annealNums]

for i in range(len(x)):
    wr.writerow([x[i]] + [metricData[j][i+1] for j in range(len(metricData))])

f.close()

#Now plot the results
labels = ['Paramerter Space Metric1', 'Paramerter Space Metric2', 'Paramerter Space Metric3', 'Objective Space Metric1', 'Objective Space Metric2', 'Objective Space Metric3']

for i in range(6):
    plot.subplot(2,3, i + 1)
    plot.plot(x, metricData[i][1:])
    plot.xlabel('Number of measurements')
    plot.ylabel(labels[i])

plot.show()
