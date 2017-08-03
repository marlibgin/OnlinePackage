'''
DLS-OnlineOptimiser: A flexible online optimisation package for use on the Diamond machine.
Version 3
@authors: David Obee, James Rogers and Greg Henderson.
'''


from __future__ import division
print 'Welcome to DLS-OnlineOptimiser'
print 'Loading...'

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
import cothread

import numpy
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm

import dls_optimiser_util as util
#import dls_optimiser_plot as plot
import dls_optimiser_plot as plot

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output)


''' Global variables and algorithm setup space '''
#class my_interactor(util.dls_machine_interactor_base):
#class my_interactor(util.kur_simulation_interactor_base):
#    pass

# To use the model change util.dls_machine_interactor_bulk_base to util.sim_machine_interactor_bulk_base
# class modified_interactor(util.dls_machine_interactor_bulk_base):
initial_settings = None
#used below in run optimiser
#The two classes below are for simulated interaction and machine interaction respectively.
class modified_interactor1(util.sim_machine_interactor_bulk_base):
    def mr_to_ar(self, mrs):

        ars = []

        #for mr, mapping in zip(mrs, mr_to_ar_mapping):
        #    ars.append(mapping(mr))
        mr_to_ar_sign = [mrr.mr_to_ar_sign for mrr in results]
        for mr, sign in zip(mrs, mr_to_ar_sign):
            if sign == '+':
                ars.append(mr)
            elif sign == '-':
                ars.append(-mr)

        return ars

class modified_interactor2(util.dls_machine_interactor_bulk_base):
    def mr_to_ar(self, mrs):

        ars = []

        #for mr, mapping in zip(mrs, mr_to_ar_mapping):
        #    ars.append(mapping(mr))
        mr_to_ar_sign = [mrr.mr_to_ar_sign for mrr in results]
        for mr, sign in zip(mrs, mr_to_ar_sign):
            if sign == '+':
                ars.append(mr)
            elif sign == '-':
                ars.append(-mr)

        return ars



class mp_group_representation:

    def __init__(self):

        self.mp_representations = []
        self.list_iid = None
        self.ap_label = None
        self.relative_setting = None
        self.ap_min = None
        self.ap_max = None


class mp_representation:

    def __init__(self):

        self.mp_obj = None
        self.list_iid = None
        #self.mp_min = None
        #self.mp_max = None
        self.mp_label = None


class mr_representation:

    def __init__(self):

        self.mr_obj = None
        self.list_iid = None
        self.mr_label = None
        self.ar_label = None
        self.mr_to_ar_sign = None
        self.max_min_text = None
        self.max_min_sign = None




#mr_to_ar_mapping = []
mr_to_ar_sign = []

keepUpdating = True

optimiserNames = ('Multi-Objective Particle Swarm Optimiser (MOPSO)',
                  'Multi-Objective Simulated Annealing (MOSA)',
                  'Multi-Objective Non-dominated Sorting Genetic Algorithm (NSGA-II)',
                  'Single-Objective Robust Conjugate Direction Search (RCDS)')

optimiserFiles = {'Multi-Objective Particle Swarm Optimiser (MOPSO)': 'dlsoo_mopso.py',
                  'Multi-Objective Simulated Annealing (MOSA)': 'dlsoo_mosa.py',
                  'Multi-Objective (NSGA-II)': 'dlsoo-nsga2.py',
                  'Single-Objective Robust Conjugate Direction Search (RCDS)': 'dlsoo_rcds.py'}

interactor = None
optimiser = None
useMachine = False
signConverter = []
#Sign converter converts algo params to machine params. This is used in the plotting below.

mp_addresses = []
mr_addresses = []

mp_min_var = []
mp_max_var = []

ap_min_var = []
ap_max_var = []

relative_settings = []

optimiser_wrapper_address = None
optimiser_wrapper = None

store_address = None

algo_settings_dict = None

mp_labels = []
mr_labels = []
ap_labels = []
ar_labels = []


parameters = []
results = []









''' Main window '''
class main_window(Tkinter.Frame):

    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

        self.initUi()

    def initUi(self):

        self.parent.title("DLS Machine Optimiser")

        self.parent.columnconfigure(0, weight=1)
        self.parent.columnconfigure(1, weight=1)
        self.parent.columnconfigure(2, weight=1)
        self.parent.columnconfigure(3, weight=1)
        self.parent.columnconfigure(4, weight=1)
        self.parent.columnconfigure(5, weight=1)

        self.Tinput_params = ttk.Treeview(self.parent, columns=("lb", "ub", "delay"))
        self.Tinput_params.column("lb", width=120)
        self.Tinput_params.heading("lb", text="Lower bound")
        self.Tinput_params.column("ub", width=120)
        self.Tinput_params.heading("ub", text="Upper bound")
        self.Tinput_params.column("delay", width=80)
        self.Tinput_params.heading("delay", text="Delay /s")
        self.Tinput_params.grid(row=0, column=0, columnspan=3)

        self.Toutput_params = ttk.Treeview(self.parent, columns=("counts", "delay", "maxmin"))
        self.Toutput_params.column("counts", width=120)
        self.Toutput_params.heading("counts", text="Min. Counts")
        self.Toutput_params.column("delay", width=120)
        self.Toutput_params.heading("delay", text="Delay /s")
        self.Toutput_params.column("maxmin", width=80)
        self.Toutput_params.heading("maxmin", text="Target")
        self.Toutput_params.grid(row=0, column=3, columnspan=3)

        self.btn_input_params_add = Tkinter.Button(self.parent, text="Add single", command=self.show_add_pv_window)
        self.btn_input_params_add.grid(row=1, column=0, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_input_params_addbulk = Tkinter.Button(self.parent, text="Add group", command=self.show_add_bulk_pv_window)
        self.btn_input_params_addbulk.grid(row=2, column=0, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_input_params_rmv = Tkinter.Button(self.parent, text="Remove", command=self.remove_pv)
        self.btn_input_params_rmv.grid(row=1, column=2, rowspan=2, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)

        self.btn_output_params_add = Tkinter.Button(self.parent, text="Add", command=self.show_add_obj_func_window)
        self.btn_output_params_add.grid(row=1, column=3, rowspan=2, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_output_params_rmv = Tkinter.Button(self.parent, text="Remove", command=self.remove_obj)
        self.btn_output_params_rmv.grid(row=1, column=5, rowspan=2, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)

        #self.Tinput_params.insert('', 'end', text="Hello world!")
        ttk.Separator(self.parent, orient='horizontal').grid(row=3, column=0, columnspan=6, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        Tkinter.Label(self.parent, text="Save directory:").grid(row=4, column=0, sticky=Tkinter.E)
        self.i_save_address = Tkinter.Entry(self.parent)
        self.i_save_address.grid(row=4, column=1, columnspan=4, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)
        self.btn_browse_save_address = Tkinter.Button(self.parent, text="Browse...", command=self.browse_save_location)
        self.btn_browse_save_address.grid(row=4, column=5, sticky=Tkinter.E+Tkinter.W)

        ttk.Separator(self.parent, orient='horizontal').grid(row=5, column=0, columnspan=6, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        self.optimiserChoice = Tkinter.StringVar()
        Tkinter.Label(self.parent, text="Algorithm:").grid(row=6, column=0, sticky=Tkinter.E)
        self.algo = ttk.Combobox(self.parent, textvariable=self.optimiserChoice, values=optimiserNames)
        self.algo.grid(row=6, column=1, columnspan=4, sticky=Tkinter.E+Tkinter.W+Tkinter.N+Tkinter.S)

        ttk.Separator(self.parent, orient='horizontal').grid(row=7, column=0, columnspan=6, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        self.btn_algo_settings = Tkinter.Button(self.parent, text="Next...", bg="red", command=self.next_button)
        self.btn_algo_settings.grid(row=8, column=5, sticky=Tkinter.E+Tkinter.W)

        self.btn_debug_setup = Tkinter.Button(self.parent, text="Debug Setup*")
        self.btn_debug_setup.grid(row=8, column=4, sticky=Tkinter.E+Tkinter.W)

        self.btn_load_config = Tkinter.Button(self.parent, text="Load configuration", command=self.load_config)
        self.btn_load_config.grid(row=8, column=0, sticky=Tkinter.E+Tkinter.W)

        self.btn_save_config = Tkinter.Button(self.parent, text="Save configuration", command=self.save_config)
        self.btn_save_config.grid(row=8, column=1, sticky=Tkinter.E+Tkinter.W)

    def browse_save_location(self):
        global store_address
        current_time_string = datetime.datetime.fromtimestamp(time.time()).strftime('%d.%m.%Y_%H.%M.%S')
        store_directory = tkFileDialog.askdirectory()
        self.i_save_address.delete(0, 'end')
        self.i_save_address.insert(0, store_directory)
        store_address = '{0}/Optimisation@{1}'.format(store_directory, current_time_string)
        if not os.path.exists(store_address):                                               #make save directory
            os.makedirs(store_address)
        print store_address

    def show_add_pv_window(self):
        add_pv_window.deiconify()

    def show_add_bulk_pv_window(self):
        add_bulk_pv_window.deiconify()

    def show_add_obj_func_window(self):
        add_obj_func_window.deiconify()

    def remove_pv(self):

        iid = self.Tinput_params.selection()[0]
        print "REMOVE PV"
        print "Selected iid: {0}".format(iid)

        for mpgrn, mpgr in enumerate(parameters):
            print mpgr.list_iid
            if mpgr.list_iid == iid:
                self.Tinput_params.delete(iid)
                del parameters[mpgrn]





    def remove_obj(self):
        print "REMOVE OBJ"
        iid = self.Toutput_params.selection()[0]

        for mrrn, mrr in enumerate(results):

            if mrr.list_iid == iid:
                self.Toutput_params.delete(iid)
                del results[mrrn]


    def next_button(self):
        global optimiser_wrapper_address
        optimiser_wrapper_address = optimiserFiles[self.optimiserChoice.get()]
        add_obj_func_window.withdraw()
        add_pv_window.withdraw()
        add_bulk_pv_window.withdraw()

        self.parent.withdraw()
        algorithm_settings_frame.load_algo_frame(optimiser_wrapper_address)
        algorithm_settings_frame.initUi()
        algorithm_settings_window.deiconify()

    def load_config(self):
        print "LOAD CONFIG"
        config_file = tkFileDialog.askopenfile()

        config = pickle.load(config_file)

        global parameters
        global results


        parameters += config['parameters']
        results += config['results']



        config_file.close()

        self.Tinput_params.delete(*self.Tinput_params.get_children())
        self.Toutput_params.delete(*self.Toutput_params.get_children())

        for mpgr in parameters:

            if len(mpgr.mp_representations) == 1:
                mpr = mpgr.mp_representations[0]
                iid = self.Tinput_params.insert('', 'end', text=mpr.mp_label, values=(mpgr.ap_min, mpgr.ap_max, mpr.mp_obj.delay))
                print "Single iid: {0}".format(iid)
                mpgr.list_iid = iid
                mpr.list_iid = iid

            else:
                parent_iid = self.Tinput_params.insert('', 'end', text=mpgr.ap_label, values=(mpgr.ap_min, mpgr.ap_max, mpgr.mp_representations[0].mp_obj.delay))
                mpgr.list_iid = parent_iid
                print "Bulk parent iid: {0}".format(parent_iid)
                for mpr in mpgr.mp_representations:
                    iid = self.Tinput_params.insert(parent_iid, 'end', text=mpr.mp_label, values=("", "", mpr.mp_obj.delay))
                    print "Bulk individual iid: {0}, belonging to parent iid: {1}".format(iid, parent_iid)
                    mpr.list_iid = iid


        for mrr in results:

            iid = self.Toutput_params.insert('', 'end', text=mrr.mr_label, values=(mrr.mr_obj.min_counts, mrr.mr_obj.delay, mrr.max_min_text))
            mrr.list_iid = iid

        print [i.list_iid for i in parameters]

    def save_config(self):

        config_file = tkFileDialog.asksaveasfile()

        global parameters
        global results

        config = {'parameters' : parameters,
                  'results' : results}

        pickle.dump(config, config_file)

        config_file.close()




class add_pv(Tkinter.Frame):

    def __init__(self, parent):
        print "INIT"
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.parent.protocol('WM_DELETE_WINDOW', self.x_button)

        self.initUi()

    def initUi(self):
        self.parent.title("Add Parameter PV")

        self.setting_mode = Tkinter.IntVar()
        self.setting_mode.set(0)

        Tkinter.Label(self.parent, text="PV address:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self.parent)
        self.i0.grid(row=0, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Lower bound/change:").grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self.parent)
        self.i1.grid(row=1, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Upper bound/change:").grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self.parent)
        self.i2.grid(row=2, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Delay /s:").grid(row=3, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self.parent)
        self.i3.grid(row=3, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.parent, text="Use as bounds", variable=self.setting_mode, value=0)
        self.r0.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)

        self.r1 = Tkinter.Radiobutton(self.parent, text="Use as change", variable=self.setting_mode, value=1)
        self.r1.grid(row=4, column=2, sticky=Tkinter.E+Tkinter.W)

        self.b1 = Tkinter.Button(self.parent, text="Cancel", command=add_pv_window.withdraw)
        self.b1.grid(row=5, column=1, sticky=Tkinter.E+Tkinter.W)
        self.b2 = Tkinter.Button(self.parent, text="OK", command=self.add_pv_to_list)
        self.b2.grid(row=5, column=2, sticky=Tkinter.E+Tkinter.W)

    def add_pv_to_list(self):
        details = (self.i0.get(), self.i1.get(), self.i2.get(), self.i3.get(), self.setting_mode.get())

        good_data = True

        try:
            float(details[1])
        except:
            good_data = False
            tkMessageBox.showerror("Input Error", "The lower bound/change cannot be converted to a float")

        try:
            float(details[2])
        except:
            good_data = False
            tkMessageBox.showerror("Input Error", "The upper bound/change cannot be converted to a float")

        try:
            float(details[3])
        except:
            good_data = False
            tkMessageBox.showerror("Input Error", "The delay cannot be converted to a float")

        if good_data:

            iid = the_main_window.Tinput_params.insert('', 'end', text=details[0], values=(details[1], details[2], details[3]))

            mpgr = mp_group_representation()
            mpr = mp_representation()
            mpr.mp_obj = util.dls_param_var(details[0], float(details[3]))
            mpr.list_iid = iid
            mpr.mp_label = details[0]

            mpgr.mp_representations.append(mpr)
            mpgr.list_iid = iid
            mpgr.ap_label = details[0]

            if details[4] == 0:
                mpgr.relative_setting = False
                mpgr.ap_min = float(details[1])
                mpgr.ap_max = float(details[2])

            elif details[4] == 1:
                mpgr.relative_setting = True
                mpgr.ap_min = float(details[1])
                mpgr.ap_max = float(details[2])


            parameters.append(mpgr)

            add_pv_window.withdraw()



    def x_button(self):
        print "Sup"
        self.parent.withdraw()


class add_bulk_pv(Tkinter.Frame):

    def __init__(self, parent):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.parent.protocol('WM_DELETE_WINDOW', self.x_button)

        self.initUi()

    def initUi(self):

        self.parent.title("Add Bulk Parameter PVs")

        self.setting_mode = Tkinter.IntVar()
        self.setting_mode.set(2)

        Tkinter.Label(self.parent, text="Group name:").grid(row=0, column=0, sticky=Tkinter.E, pady=(10, 0))
        self.i6 = Tkinter.Entry(self.parent)
        self.i6.grid(row=0, column=1, columnspan=2, sticky=Tkinter.W+Tkinter.E, pady=(10, 0), padx=(0, 10))

        ttk.Separator(self.parent, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky=Tkinter.E+Tkinter.W, padx=10, pady=10)

        Tkinter.Label(self.parent, text="PV addresses:").grid(row=2, column=0, sticky=Tkinter.E+Tkinter.W)
        Tkinter.Label(self.parent, text="Lower bounds:").grid(row=2, column=1, sticky=Tkinter.E+Tkinter.W)
        Tkinter.Label(self.parent, text="Upper bounds:").grid(row=2, column=2, sticky=Tkinter.E+Tkinter.W)

        self.i0 = Tkinter.Text(self.parent, width=40)
        self.i0.grid(row=3, column=0, sticky=Tkinter.E+Tkinter.W)
        self.i1 = Tkinter.Text(self.parent, width=40)
        self.i1.grid(row=3, column=1, sticky=Tkinter.E+Tkinter.W)
        self.i2 = Tkinter.Text(self.parent, width=40)
        self.i2.grid(row=3, column=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Change:").grid(row=4, column=0, sticky=Tkinter.E)

        self.i4 = Tkinter.Entry(self.parent)
        self.i4.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)

        self.i5 = Tkinter.Entry(self.parent)
        self.i5.grid(row=4, column=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Delay:").grid(row=5, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self.parent)
        self.i3.grid(row=5, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.parent, text="Relative from bounds", variable=self.setting_mode, value=0)
        self.r0.grid(row=6, column=1)

        self.r1 = Tkinter.Radiobutton(self.parent, text="Absolute from bounds", variable=self.setting_mode, value=1)
        self.r1.grid(row=6, column=2)

        self.r2 = Tkinter.Radiobutton(self.parent, text="Relative with change", variable=self.setting_mode, value=2)
        self.r2.grid(row=6, column=0)

        self.b0 = Tkinter.Button(self.parent, text="Cancel", command=self.parent.withdraw)
        self.b0.grid(row=7, column=1, sticky=Tkinter.E+Tkinter.W)

        self.b1 = Tkinter.Button(self.parent, text="Add", command=self.add_pvs)
        self.b1.grid(row=7, column=2, sticky=Tkinter.E+Tkinter.W)


    def add_pvs(self):

        details = (self.i0.get(0.0, Tkinter.END), self.i1.get(0.0, Tkinter.END), self.i2.get(0.0, Tkinter.END), self.i4.get(), self.i5.get(), self.i3.get(), self.setting_mode.get())
        processed_details = [[], [], [], None, None, None, None] # This will contain PVs, lb, ub, lc, uc, delay, and setting_mode

        for address in details[0].splitlines():
            processed_details[0].append(address)

        for lower,  upper in zip(details[1].splitlines(), details[2].splitlines()):
            processed_details[1].append(lower)
            processed_details[2].append(upper)

        processed_details[3] = details[3]
        processed_details[4] = details[4]

        processed_details[5] = details[5]
        processed_details[6] = details[6]

        # Check that the data is all of the correct format
        good_data = True
        for i in range(len(processed_details[1])):
            try:
                if processed_details[6] in [0, 1]:
                    processed_details[1][i] = float(processed_details[1][i])
            except:
                tkMessageBox.showerror("Format error with lower bound", "The lower bound value for PV #{0}: \"{1}\", could not be converted to a float. Please check the values you have entered.".format(i+1, processed_details[1][i]))
                good_data = False

        for i in range(len(processed_details[2])):
            try:
                if processed_details[6] in [0, 1]:
                    processed_details[2][i] = float(processed_details[2][i])
            except:
                tkMessageBox.showerror("Format error with upper bound", "The upper bound value for PV #{0}: \"{1}\", could not be converted to a float. Please check the values you have entered.".format(i+1, processed_details[2][i]))
                good_data = False

        try:
            if processed_details[6] == 2:
                processed_details[3] = float(processed_details[3])
        except:
            tkMessageBox.showerror("Format error with lower change", "The lower change value: \"{0}\", could not be converted to a float. Please check the value you have entered.".format(processed_details[3]))
            good_data = False

        try:
            if processed_details[6] == 2:
                processed_details[4] = float(processed_details[4])
        except:
            tkMessageBox.showerror("Format error with upper change", "The upper change value: \"{0}\", could not be converted to a float. Please check the value you have entered.".format(processed_details[4]))
            good_data = False

        try:
            processed_details[5] = float(processed_details[5])
        except:
            tkMessageBox.showerror("Format error with delay", "The delay value: \"{0}\", could not be converted to a float. Please check the value you have entered.".format(processed_details[5]))
            good_data = False

        if good_data:

            mpgr = mp_group_representation()

            #mp_representations = []

            for pv in processed_details[0]:
                pv = pv.encode('ascii', 'ignore')
                mpr = mp_representation()
                mpr.mp_obj = util.dls_param_var(pv, processed_details[5])
                mpr.mp_label = pv
                print pv
                #mp_representations.append(mpr)
                mpgr.mp_representations.append(mpr)
            print "processed_details[0]: {0}".format(processed_details[0])
            print "mpgr to be added: {0}".format([i.mp_label for i in mpgr.mp_representations])
            if useMachine:
                temp_interactor = modified_interactor2(param_var_groups=[[i.mp_obj for i in mpgr.mp_representations]])
            else:
                temp_interactor = modified_interactor1(param_var_groups=[[i.mp_obj for i in mpgr.mp_representations]])
            initial_mps = temp_interactor.get_mp()

            if processed_details[6] == 0:
                # This means we are setting according to the bounds

                # Calculate relative from bounds

                a_min, a_max = util.find_group_a_bounds(processed_details[1], processed_details[2], initial_mps, True)

                mpgr.relative_setting = True
                mpgr.ap_min = a_min
                mpgr.ap_max = a_max



            elif processed_details[6] == 1:
                # This means we are setting according to the bounds

                # Calculate absolute from bounds

                a_min, a_max = util.find_group_a_bounds(processed_details[1], processed_details[2], initial_mps, False)

                mpgr.relative_setting = False
                mpgr.ap_min = a_min
                mpgr.ap_max = a_max



            elif processed_details[6] == 2:
                # This means we are setting according to the change, not the bounds

                # Calculate relative from change

                mpgr.relative_setting = True
                mpgr.ap_min = processed_details[3]
                mpgr.ap_max = processed_details[4]

                processed_details[1] = ["" for i in processed_details[0]]
                processed_details[2] = ["" for i in processed_details[0]]


            parent_iid = the_main_window.Tinput_params.insert('', 'end', text=self.i6.get(), values=(mpgr.ap_min, mpgr.ap_max, processed_details[5]))
            mpgr.list_iid = parent_iid

            for i, mpr in enumerate(mpgr.mp_representations):
                print "ADDING"
                iid = the_main_window.Tinput_params.insert(parent_iid, 'end', text=processed_details[0][i], values=(processed_details[1][i], processed_details[2][i], processed_details[5]))
                mpr.list_iid = iid


            mpgr.ap_label = self.i6.get()

            parameters.append(mpgr)




            add_bulk_pv_window.withdraw()


    def x_button(self):
        print "Sup"
        self.parent.withdraw()


class add_obj_func(Tkinter.Frame):

    def __init__(self, parent):
        print "INIT"
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent
        self.parent.protocol('WM_DELETE_WINDOW', self.x_button)

        self.initUi()

    def initUi(self):
        self.parent.title("Add Objective PV")

        self.max_min_setting = Tkinter.IntVar()
        self.max_min_setting.set(0)

        Tkinter.Label(self.parent, text="PV address:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self.parent)
        self.i0.grid(row=0, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Min. count:").grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self.parent)
        self.i1.grid(row=1, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        Tkinter.Label(self.parent, text="Delay /s:").grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self.parent)
        self.i2.grid(row=2, column=1, columnspan=2, sticky=Tkinter.E+Tkinter.W)

        self.r0 = Tkinter.Radiobutton(self.parent, text="Minimise", variable=self.max_min_setting, value=0)
        self.r0.grid(row = 3, column=0, sticky=Tkinter.W)
        self.r1 = Tkinter.Radiobutton(self.parent, text="Maximise", variable=self.max_min_setting, value=1)
        self.r1.grid(row = 3, column=1, sticky=Tkinter.W)

        self.b1 = Tkinter.Button(self.parent, text="Cancel", command=add_obj_func_window.withdraw)
        self.b1.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)
        self.b2 = Tkinter.Button(self.parent, text="OK", command=self.add_pv_to_list)
        self.b2.grid(row=4, column=2, sticky=Tkinter.E+Tkinter.W)

    def add_pv_to_list(self):
        global results

        mrr = mr_representation()
        mrr.mr_obj = util.dls_measurement_var(self.i0.get(), float(self.i1.get()), float(self.i2.get()))

        if self.max_min_setting.get() == 0:
            mrr.max_min_text = "Minimise"
            mrr.max_min_sign = "+"
            mrr.mr_to_ar_sign = "+"
        elif self.max_min_setting.get() == 1:
            mrr.max_min_text = "Maximise"
            mrr.max_min_sign = "-"
            mrr.mr_to_ar_sign = "-"

        iid = the_main_window.Toutput_params.insert('', 'end', text=self.i0.get(), values=(self.i1.get(), self.i2.get(), mrr.max_min_text))
        mrr.list_iid = iid
        mrr.mr_label = self.i0.get()
        mrr.ar_label = self.i0.get()

        results.append(mrr)

        add_obj_func_window.withdraw()

    def x_button(self):
        print "Sup"
        self.parent.withdraw()



class show_progress(Tkinter.Frame):

    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

        #self.initUi()

    def initUi(self):
        global signConverter
        #redstyle = ttk.Style()
        #redstyle.theme_use("clam")
        #redstyle.configure("red.Horizontal.TProgressbar", foreground="red", background="red")
        self.parent.title("Optimising...")

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

        self.pbar_progress = ttk.Progressbar(self.parent, length=400, variable=progress)
        self.pbar_progress.grid(row=0, column=0, columnspan=4, padx=10, pady=10)
        #self.pbar_progress.pack()

        self.strip_plot = strip_plot(self.parent)
        self.strip_plot.grid(row=2, column=0, columnspan=4)

        #self.lbl_percentage = Tkinter.Label(self.parent, text="0%")
        #self.lbl_percentage.grid(row=1, column=0)
        self.btn_cancel = Tkinter.Button(self.parent, text="Cancel", command=self.cancelMethod)
        self.btn_cancel.grid(row=1, column=3, sticky=Tkinter.W+Tkinter.E)
        #self.btn_cancel.pack()

        self.btn_pause = Tkinter.Button(self.parent, text="Pause", command=self.pause_algo)
        self.btn_pause.grid(row=1, column=2, sticky=Tkinter.E+Tkinter.W)

        # This part will display the latest plot
        ar_labels = [mrr.ar_label for mrr in results]
        self.progress_plot = optimiser_wrapper.import_algo_prog_plot(self.parent, ar_labels, signConverter)
        self.progress_plot.grid(row=3, column=0, columnspan=4)
        print "UI INIT"

        #self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.parent)
        #self.toolbar.update()
        #self.canvas._tkcanvas.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)




    def handle_progress(self, normalised_percentage, generation):
        #self.pbar_progress.step(1/max_gen * 100)
        #root.update()

        #if generation >= 1:
            #plot.intermediate_plot("{0}/fronts.{1}".format(the_main_window.i_save_address.get(), generation-1))

        progress.set(normalised_percentage * 100)
        progress_frame.update()
        #print 'testing'
        self.strip_plot.update()

        self.progress_plot.update()


    def pause_algo(self):
        print "This works"
        global optimiser
        optimiser.pause = not optimiser.pause

        if optimiser.pause:
            self.btn_pause.config(text="Unpause")
            self.parent.config(background="red")
        else:
            self.btn_pause.config(text="Pause")
            self.parent.config(background="#d9d9d9")

    def cancelMethod(self):
        optimiser.cancel = True


class plot_progress(Tkinter.Frame):

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


class strip_plot(Tkinter.Frame):

    def __init__(self, parent):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

        self.initUi()

    def initUi(self):
        global interactor
        self.interactor = interactor
        self.data_sets = []
        self.time_sets = []
        self.initTime = time.time()

        self.fig = Figure(figsize=(5, 1), dpi=100)
        self.a = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)

    def update(self):

        mps = self.interactor.get_mp()
        mrs = []
        for i in self.interactor.measurement_vars:
            mrs.append(self.interactor.get_pv(i.pv))

        new_data = mrs + mps
        self.data_sets.append(new_data)
        self.time_sets.append(time.time() - self.initTime)

        plot.plot_strip_tool(self.a, self.data_sets, self.time_sets)
        self.canvas.show()





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
        
        global signConverter

        ''' First, unpickle the mp_to_ap mapping file '''

        mapping_file = open("{0}/ap_to_mp_mapping_file.txt".format(store_address))
        mp_to_ap_mapping = pickle.load(mapping_file)
        mapping_file.close()

        ''' Now get the mp values '''

        mps = mp_to_ap_mapping[aps]
        self.mps = mps

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
            tree_ar.insert('', 'end', text=results[i].ar_label, values=(signConverter[i]*ar))

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



class algorithm_settings(Tkinter.Frame):

    def __init__(self, parent):

        Tkinter.Frame.__init__(self, parent)

        self.parent = parent

    def initUi(self):

        self.parent.title("Algorithm settings")

        self.algo_frame.grid(row=0, column=0, columnspan=2, sticky=Tkinter.N+Tkinter.E+Tkinter.S+Tkinter.W, pady=10, padx=10)

        ttk.Separator(self.parent, orient="horizontal").grid(row=1, pady=10, padx=10, sticky=Tkinter.E+Tkinter.W, columnspan=2)

        b0 = Tkinter.Button(self.parent, text="Start...", bg="red", command=self.set_settings)
        b0.grid(row=2, column=1, sticky=Tkinter.E+Tkinter.W)


    def load_algo_frame(self, file_address):
        #execfile(file_address, globals())
        global optimiser_wrapper
        optimiser_wrapper = imp.load_source(os.path.splitext(os.path.split(file_address)[1])[0], file_address)
        self.algo_frame = optimiser_wrapper.import_algo_frame(self.parent)

    def set_settings(self):
        global algo_settings_dict
        global optimiser
        global optimiser_wrapper
        global interactor
        global parameters
        global results
        global signConverter
        global store_address
        algo_settings_dict = self.algo_frame.get_dict()

        if algo_settings_dict == "error":
            tkMessageBox.showerror("Algorithm settings error", "There was an error in one or more of the settings given. The optimisation procedure will not proceed.")
        else:
            interactorIdentity = ''
            if useMachine:
                interactorIdentity = 'MACHINE'
            else:
                interactorIdentity = 'SIMULATOR'
            userContinue = tkMessageBox.askyesno(title='READY?', message='You are using the ' + interactorIdentity + '. ' + 'Are you sure you wish to start optimisation?', icon=tkMessageBox.WARNING)
            if userContinue:
                mp_addresses = [[mpr.mp_obj for mpr in mpgr.mp_representations] for mpgr in parameters]
                mr_addresses = [mrr.mr_obj for mrr in results]
                relative_settings = [mpgr.relative_setting for mpgr in parameters]
                ap_min_var = [mpgr.ap_min for mpgr in parameters]
                ap_max_var = [mpgr.ap_max for mpgr in parameters]
                for mrr in results:
                    if mrr.mr_to_ar_sign == '-':
                        signConverter.append(-1)
                    else:
                        signConverter.append(1)
                if useMachine:
                    interactor = modified_interactor2(mp_addresses, mr_addresses, set_relative=relative_settings)
                else:
                    interactor = modified_interactor1(mp_addresses, mr_addresses, set_relative=relative_settings)
                
                save_object(interactor, '{0}/interactor'.format(store_address))

                #ap_min_var, ap_max_var = interactor.find_a_bounds(mp_min_var, mp_max_var)
                #print ap_min_var
                #print ap_max_var
                initial_mp = interactor.get_mp()
                #print mr_addresses
                optimiser = optimiser_wrapper.optimiser(settings_dict=algo_settings_dict,
                                                        interactor=interactor,
                                                        store_location=store_address,
                                                        a_min_var=ap_min_var,
                                                        a_max_var=ap_max_var,
                                                        progress_handler=progress_frame.handle_progress) # Still need to add the individuals, and the progress handler

                self.parent.withdraw()
                run_optimisation()

class interactor_selector_frame(Tkinter.Frame):
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)
        root.withdraw()
        self.parent = parent
        self.grid()
        self.iChoice = Tkinter.StringVar()
        self.iChoice.set('Simulator')
        self.question1 = Tkinter.Label(self, text='Which interactor are you intending to use?')
        self.question1.grid(row=0, column=0)
        self.optList = ttk.Combobox(self, textvariable=self.iChoice, values=('Machine', 'Simulator'))
        self.optList.grid(row=1,column=0)
        self.subBtn = Tkinter.Button(self, text='Continue', command=self.setInteractor)
        self.subBtn.grid(row=2, column=0)

    def setInteractor(self):
        global useMachine
        item = self.iChoice.get()
        if item == 'Machine':
            useMachine = True
            self.parent.withdraw()
            root.deiconify()
        elif item == 'Simulator':
            useMachine = False
            self.parent.withdraw()
            root.deiconify()




def main_window_lock_unlock(new_state):
    the_main_window.btn_algo_settings.config(state=new_state)
    the_main_window.btn_browse_address.config(state=new_state)
    the_main_window.btn_input_params_add.config(state=new_state)
    the_main_window.btn_input_params_rmv.config(state=new_state)
    the_main_window.btn_output_params_add.config(state=new_state)
    the_main_window.btn_output_params_rmv.config(state=new_state)
    the_main_window.btn_run.config(state=new_state)


def save_details_files(start_time, end_time):
    global my_solver
    global the_interactor
    global store_address

    f = file("{0}/algo_details.txt".format(store_address), "w")
    f.write(optimiser.save_details_file())

    f = file("{0}/inter_details.txt".format(store_address), "w")
    f.write(interactor.save_details_file())

    f = file("{0}/controller_details.txt".format(store_address), "w")
    f.write("Controller\n")
    f.write("==========\n\n")

    f.write("Start time: {0}-{1}-{2} {3}:{4}:{5}\n".format(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute, start_time.second))
    f.write("End time: {0}-{1}-{2} {3}:{4}:{5}\n".format(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute, end_time.second))



def run_optimisation():
    global final_plot_frame
    global initial_settings
    print "Lets go!"
    #print mp_labels
    #print ap_labels
    #print mr_labels
    #print mr_labels
    #time.sleep(100)

    progress_frame.initUi()
    algorithm_settings_window.withdraw()

    initial_settings = interactor.get_mp()

    progress_window.deiconify()
    progress_window.grab_set()
    cothread.Spawn(optimiserThreadMethod)


def optimiserThreadMethod():
    global signConverter
    global final_plot_frame
    global optimiser
    global parameters
    global results
    global store_address
    global keepUpdating
    
    if not os.path.exists('{0}/FRONTS'.format(store_address)):
        os.makedirs('{0}/FRONTS'.format(store_address))
        
    start_time = time.time()

    optimiser.optimise()
    #print results
    keepUpdating = False

    end_time = time.time()

    interactor.set_mp(initial_settings)
    save_details_files(datetime.datetime.fromtimestamp(start_time), datetime.datetime.fromtimestamp(end_time))
    
    if not os.path.exists('{0}/PARAMETERS'.format(store_address)):
        os.makedirs('{0}/PARAMETERS'.format(store_address))
        
    if not os.path.exists('{0}/RESULTS'.format(store_address)):
        os.makedirs('{0}/RESULTS'.format(store_address))
        
    for i in range(len(parameters)):
        save_object(parameters[i], '{0}/PARAMETERS/parameter_{1}'.format(store_address, i))
    for i in range(len(results)):
        save_object(results[i], '{0}/RESULTS/result_{1}'.format(store_address, i))
    
    
    
    signConverter_file = open("{0}/signConverter.txt".format(store_address), 'w')
    signConverter_file.write(str(signConverter))
    signConverter_file.close()
    
    ap_to_mp_mapping_file = open("{0}/ap_to_mp_mapping_file.txt".format(store_address), 'w')
    ap_to_mp_mapping_file.write(interactor.string_ap_to_mp_store())
    ap_to_mp_mapping_file.close()

    ''' By this point, the algorithm has finished the optimisation, and restored the machine '''

    progress_window.grab_release()
    progress_window.withdraw()

    ar_labels = [mrr.ar_label for mrr in results]
    final_plot_frame = optimiser_wrapper.import_algo_final_plot(final_plot_window, point_frame.generateUi, ar_labels, signConverter)
    final_plot_frame.initUi()
    final_plot_window.deiconify()











root = Tkinter.Tk()
root.title("DLS Online Optimiser")
rootInit = Tkinter.Toplevel(root)
rootInit.title('DLS Interactor Selector')
initter = interactor_selector_frame(rootInit)

def yielder():
    cothread.Yield()
    root.after(100, yielder)
root.after(100, yielder)

progress = Tkinter.DoubleVar()
progress.set(0.00)

# The main setup window
the_main_window = main_window(root)

# The dialog for adding input parameters
add_pv_window = Tkinter.Toplevel(root)
add_pv_frame = add_pv(add_pv_window)
add_pv_window.withdraw()
#print add_pv_window.cget("bg")

# The dialog for adding objective functions
add_obj_func_window = Tkinter.Toplevel(root)
add_obj_func_frame = add_obj_func(add_obj_func_window)
add_obj_func_window.withdraw()

# The dialog showing calculation progress
progress_window = Tkinter.Toplevel(root)
progress_frame = show_progress(progress_window)
progress_window.withdraw()

point_window = Tkinter.Toplevel(root)
point_frame = point_details(point_window)
point_window.withdraw()

final_plot_window = Tkinter.Toplevel(root)
#final_plot_frame = display_final_plot(final_plot_window)
final_plot_window.withdraw()

add_bulk_pv_window = Tkinter.Toplevel(root)
add_bulk_pv_frame = add_bulk_pv(add_bulk_pv_window)
add_bulk_pv_window.withdraw()

algorithm_settings_window = Tkinter.Toplevel(root)
algorithm_settings_frame = algorithm_settings(algorithm_settings_window)
algorithm_settings_window.withdraw()
#algorithm_settings_frame.load_algo_frame("/dls/physics/students/zex19517/main_implementations/GUI/update_20160805/test_algo_module.py")
#algorithm_settings_frame.initUi()

@cothread.Spawn
def ticker():
    while True:
        #print 'tick'
        cothread.Sleep(5)



root.mainloop()
print 'returned from mainloop'
cothread.WaitForQuit()