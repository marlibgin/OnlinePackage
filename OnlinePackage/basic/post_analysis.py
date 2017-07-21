'''
ANALYSIS TOOL for use of past optimisations in DLS OnlineOptimiser package

Created on 19 Jul 2017

@author: James Rogers
'''

from __future__ import division

import pkg_resources
from audioop import avg
pkg_resources.require('cothread')
pkg_resources.require('matplotlib')
pkg_resources.require('numpy')
pkg_resources.require('scipy')

import sys
import Tkinter
import ttk
import tkFileDialog
import tkMessageBox
import os
import time
import datetime
import imp
import pickle

import numpy
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm

import dls_optimiser_util as util
import dls_optimiser_plot as plot

store_address = None
algorithm_name = ""
algo_frame = None
optimiser_wrapper = None


print os.getcwd()
class main_window(Tkinter.Frame):
    
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)
        
        self.parent = parent
        
        self.initUi()
    
    def initUi(self):
        
        self.parent.columnconfigure(0, weight=1)
        self.parent.columnconfigure(1, weight=4)
        self.parent.columnconfigure(2, weight=1)
        self.parent.columnconfigure(3, weight=1)
        
        self.parent.title("DLS Post Optimisation Analysis")
        
        
        Tkinter.Label(self.parent, text="Data directory:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i_save_address = Tkinter.Entry(self.parent)
        self.i_save_address.grid(row=0, column=1, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_browse_save_address = Tkinter.Button(self.parent, text="Browse...", command=self.browse_save_location)
        self.btn_browse_save_address.grid(row=0, column=2, sticky=Tkinter.E+Tkinter.W)
        
        self.btn_algo_settings = Tkinter.Button(self.parent, text="Next...", bg="green", command=self.next_button)
        self.btn_algo_settings.grid(row=0, column=3, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self.parent, text="", justify=Tkinter.LEFT).grid(row=1, column=0, columnspan=4, sticky=Tkinter.W)
        
        ttk.Separator(self.parent, orient='horizontal').grid(row=2, column=0, columnspan=4, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)
        
        Tkinter.Label(self.parent, text="Please choose a directory in which optimisation data files have been saved.", justify=Tkinter.LEFT).grid(row=3, column=0, columnspan=4, sticky=Tkinter.W)
        
                
    def browse_save_location(self):
        
        global store_address
        global algorithm_name

        
        good_file = False
        
        store_directory = tkFileDialog.askdirectory()
        self.i_save_address.delete(0, 'end')
        self.i_save_address.insert(0, store_directory)
        store_address = store_directory
        
        if os.path.isfile('{0}/algo_details.txt'.format(store_address)): 
            algo_details = open('{0}/algo_details.txt'.format(store_address), 'r')
            data = algo_details.read()
            for i in data:
                if i == ' ':
                    good_file = True
                    break
                algorithm_name += str(i)
            
        else:
            tkMessageBox.showerror("Directory Error", "The selected directory does no contain the correct files. Please try again")
            good_file = False
        
        Tkinter.Label(self.parent, text="{0} algorithm data directory detected".format(algorithm_name), justify=Tkinter.LEFT).grid(row=1, column=0, columnspan=4, sticky=Tkinter.W+Tkinter.S)
        
        return good_file
    
    def load_algo_frame(self, file_address):
        #execfile(file_address, globals())
        global optimiser_wrapper
        optimiser_wrapper = imp.load_source(os.path.splitext(os.path.split(file_address)[1])[0], file_address)
        self.algo_frame = optimiser_wrapper.import_algo_final_plot(self.parent)
    
        
    def next_button(self):
        global algorithm_name
        global store_address
        global algo_frame
        global optimiser_wrapper
            
        optimiser_wrapper = self.load_algo_frame('{0}/{1}'.format(os.getcwd(), algorithm_name))
        algo_frame = optimiser_wrapper.import_algo_final_plot(self.parent)
        
        self.parent.withdraw()



        
class point_details(Tkinter.Frame):
    
    def __init__(self, parent):
        print "INIT"
        Tkinter.Frame.__init__(self, parent)
        
        self.parent = parent
        
        self.parent.protocol('WM_DELETE_WINDOW', self.x_button)
        
        self.initUi()
    
    def initUi(self):
        self.parent.title("Point")
        
        #self.lbl_point_details = Tkinter.Label(self.parent, text="-")
        #self.lbl_point_details.grid(row=0, column=0, sticky=Tkinter.E)
        
        
    
    def generateUi(self, ars, aps):
        
        ''' First, unpickle the mp_to_ap mapping file '''
        
        mapping_file = open("{0}/ap_to_mp_mapping_file.txt".format(store_address))
        mp_to_ap_mapping = pickle.load(mapping_file)
        mapping_file.close()
        
        ''' Now get the mp values '''
        
        mps = mp_to_ap_mapping[aps]
        self.mps = mps
        print mp_to_ap_mapping[aps]
        
        ''' Now make UI '''
        
        Tkinter.Label(self.parent, text="Machine").grid(row=0, column=1, sticky=Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S)
        Tkinter.Label(self.parent, text="Algorithm").grid(row=0, column=2, sticky=Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S)
        Tkinter.Label(self.parent, text="Parameters").grid(row=1, column=0, sticky=Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S)
        Tkinter.Label(self.parent, text="Results").grid(row=2, column=0, sticky=Tkinter.W+Tkinter.E+Tkinter.N+Tkinter.S)
        
        tree_mp = ttk.Treeview(self.parent, columns=("value"))
        tree_mp.column("value", width=200)
        tree_mp.heading("value", text="Value")
        tree_mp.grid(row=1, column=1)
        
        tree_mr = ttk.Treeview(self.parent, columns=("value"))
        tree_mr.column("value", width=200)
        tree_mr.heading("value", text="Value")
        tree_mr.grid(row=2, column=1)
        
        tree_ap = ttk.Treeview(self.parent, columns=("value"))
        tree_ap.column("value", width=200)
        tree_ap.heading("value", text="Value")
        tree_ap.grid(row=1, column=2)
        
        tree_ar = ttk.Treeview(self.parent, columns=("value"))
        tree_ar.column("value", width=200)
        tree_ar.heading("value", text="Value")
        tree_ar.grid(row=2, column=2)
        
        btn_set = Tkinter.Button(self.parent, text="Set", command=self.set_state)
        btn_set.grid(row=3, column=2, sticky=Tkinter.W+Tkinter.E, pady=10)
        
        for i, ap in enumerate(aps):
            tree_ap.insert('', 'end', text=parameters[i].ap_label, values=(ap))
        
        for i, ar in enumerate(ars):
            tree_ar.insert('', 'end', text=results[i].ar_label, values=(ar))
        
        mp_labels = []
        for mpgr in parameters:
            for mpr in mpgr.mp_representations:
                mp_labels.append(mpr.mp_label)
        for i, mp in enumerate(mps):
            tree_mp.insert('', 'end', text=mp_labels[i], values=(mp))
        
        self.parent.deiconify()
    
    def set_state(self):
        
        interactor.set_mp(self.mps)
    
    def x_button(self):
        print "Sup"
        self.parent.withdraw()

    
    
    
    
root = Tkinter.Tk()
root.title("DLS Post Optimisation Analysis")

the_main_window = main_window(root)
root.mainloop()