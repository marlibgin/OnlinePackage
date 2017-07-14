from __future__ import division

import pkg_resources
from audioop import avg
#pkg_resources.require('cothread')
#pkg_resources.require('matplotlib')
#pkg_resources.require('numpy')

import matplotlib.pyplot as pyplot
import matplotlib.cm as cm
import numpy
import matplotlib.patches as pat




def plot_pareto_fronts(file_names, ax, axis_labels):

    global fs
    #global the_interactor

    fs = []

    for file_name in file_names:
        execfile(file_name)

        fs.append(locals()['fronts'][0])

    #the_interactor = interactor


    x_vals = []
    y_vals = []

    colors = cm.jet(numpy.linspace(0, 1, len(fs)))

    for nf, f in enumerate(fs):
        #print "\n!\n"
        for ni, i in enumerate(f):
            #print i
            x_vals.append(i[1][0])
            y_vals.append(i[1][1])
            #print "{0}$".format(x_vals)

        px_vals = [x for (x, y) in sorted(zip(x_vals, y_vals))]
        py_vals = [y for (x, y) in sorted(zip(x_vals, y_vals))]

        ax.plot(px_vals, py_vals, color=colors[nf], marker='.', picker=5)

        x_vals = []
        y_vals = []


    #cid = fig.canvas.mpl_connect('pick_event', onpick)

    ax.set_xlabel(axis_labels[0])
    ax.set_ylabel(axis_labels[1])






def plot_pareto_fronts_interactive(file_names, ax, axis_labels, interactor, callback, view_mode):

    global fs
    #global the_interactor

    fs = []

    for file_name in file_names:
        execfile(file_name)

        fs.append(locals()['fronts'][0])

    #the_interactor = interactor

    x_vals = []
    y_vals = []

    if view_mode == "No focus":

        colors = cm.jet(numpy.linspace(0, 1, len(fs)))

        for nf, f in enumerate(fs):
            #print "\n!\n"
            for ni, i in enumerate(f):
                #print i
                x_vals.append(i[1][0])
                y_vals.append(i[1][1])

                x_err = i[2][0]
                y_err = i[2][1]

                if nf == len(fs) - 1:
                    ell = pat.Ellipse(xy=(i[1][0], i[1][1]), width=x_err, height=y_err)
                    ell.set_facecolor('none')
                    ax.add_artist(ell)
                #print "{0}$".format(x_vals)

            px_vals = [x for (x, y) in sorted(zip(x_vals, y_vals))]
            py_vals = [y for (x, y) in sorted(zip(x_vals, y_vals))]

            #ax.plot(px_vals, py_vals, color=colors[nf], marker='.', picker=5)

            if nf == len(fs) - 1:
                ax.plot(px_vals, py_vals, color=colors[nf], marker='.', picker=5, linewidth=2)
            else:
                ax.plot(px_vals, py_vals, color=colors[nf], marker='.')

            x_vals = []
            y_vals = []

    elif view_mode == "Best focus":

        ax.set_axis_bgcolor('black')
        greys = numpy.linspace(0.5, 0.9, len(fs) - 1)

        for nf, f in enumerate(fs):
            print "\n!\n"
            for ni, i in enumerate(f):

                x_vals.append(i[1][0])
                y_vals.append(i[1][1])

                x_err = i[2][0]
                y_err = i[2][1]

                if nf == len(fs) - 1:
                    ell = pat.Ellipse(xy=(i[1][0], i[1][1]), width=x_err, height=y_err)
                    ell.set_facecolor('none')
                    ell.set_edgecolor('white')
                    ax.add_artist(ell)


            px_vals = [x for (x, y) in sorted(zip(x_vals, y_vals))]
            py_vals = [y for (x, y) in sorted(zip(x_vals, y_vals))]

            #if nf == len(fs) - 1:
            if nf == len(fs) - 1:
                ax.plot(px_vals, py_vals, color='y', marker='.', linewidth=3, markersize=10, picker=5)
            else:
                ax.plot(px_vals, py_vals, color="{0}".format(greys[nf]), marker='.')

            x_vals = []
            y_vals = []




    #cid = fig.canvas.mpl_connect('pick_event', onpick)

    ax.set_xlabel(axis_labels[0])
    ax.set_ylabel(axis_labels[1])









def plot_strip_tool(ax, data_sets, data_times, current_time, time_interval):

    time_shifts = []

    for i in data_times:

        indv_set_times = []

        for j in i:
            indv_set_times.append(j - current_time)

        time_shifts.append(indv_set_times)

    #print data_times
    for data_set, shift_set in zip(data_sets, time_shifts):

        ax.plot(shift_set, data_set)


    #ax.set_autoscaley_on(False)
    ax.set_xlim(time_interval)
