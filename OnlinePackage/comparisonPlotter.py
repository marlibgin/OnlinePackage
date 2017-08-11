'''
Comparison Plotter
Takes in the three csv files reads them and plots them for comparison.
'''
import csv
import numpy
import matplotlib.pyplot as plot
import matplotlib.patches as mpatches
def extractData(fileName):
    rawData = []
    f = open(fileName, 'r')
    wr = csv.reader(f)
    for row in wr:
        rawData.append(row)
    data = [[float(j[i]) for j in rawData] for i in range(7)]
    return data

#extracting data
data1 = []
data1.append(extractData('mopsoConvergenceData.csv'))
data1.append(extractData('mosaConvergenceData.csv'))
data1.append(extractData('nsga2ConvergenceData.csv'))

#Now begin the plot
col1 = ['r', 'g', 'b']
col2 = ['red', 'green', 'blue']
plotPat = [mpatches.Patch(color=col) for col in col2]
labels = ['Paramerter Space Metric1', 'Paramerter Space Metric2', 'Paramerter Space Metric3', 'Objective Space Metric1', 'Objective Space Metric2', 'Objective Space Metric3']
algLabels = ['MOPSO', 'MOSA', 'NSGA2']
for i in range(6):
    plot.subplot(2,3, i + 1)
    for j in range(len(data1)):
        plot.plot(data1[j][0], data1[j][i+1], col1[j])
    plot.xlabel('Number of measurements')
    plot.ylabel(labels[i])
    plot.legend(plotPat, algLabels)

plot.show()
