'''
Created on 7 Jul 2017

@author: James Rogers
'''
import random, sys
import time
import os

import Tkinter
import ttk
import tkMessageBox
from scipy import spatial

import dls_optimiser_plot as plot
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm
import matplotlib.pyplot as pyplot


store_address = None
completed_generation = None
pareto_front = []

# colour display codes
ansi_red = "\x1B[31m"
ansi_normal = "\x1B[0m"

# cache of solutions
memo = {}

def nothing_function(data):
    pass

class optimiser:
    
    #def __init__(self, interactor, store_location, population_size, generations, param_count, result_count, min_var, max_var, pmut=None, pcross=0.9, eta_m=20, eta_c=20, individuals=None, seed=None, progress_handler=None):
    def __init__(self, settings_dict, interactor, store_location, a_min_var, a_max_var, progress_handler=None):
        
        self.interactor = interactor
        self.store_location = store_location
        self.swarm_size = settings_dict['swarm_size']
        self.max_iter = settings_dict['max_iter']
        self.param_count = settings_dict['param_count']
        self.result_count = settings_dict['result_count']
        self.min_var = a_min_var
        self.max_var = a_max_var
        self.inertia = settings_dict['inertia']
        self.social_param = settings_dict['social_param']
        self.cognitive_param = settings_dict['cognitive_param']
        
        if progress_handler == None:
            progress_handler = nothing_function
        
        self.progress_handler = progress_handler
        
        if settings_dict['seed'] == None:
            seed = time.time()
        
        self.seed = settings_dict['seed']
        
        self.pause = False
        print "interactor.param_var_groups: {0}".format(interactor.param_var_groups)
        print "interactor.measurement_vars: {0}".format(interactor.measurement_vars)
    
#     def save_details_file(self):
#         
#         file_return = ""
#         
#         file_return += "NSGA-II algorithm\n"
#         file_return += "=================\n\n"
#         file_return += "Generations: {0}\n".format(self.generations)
#         file_return += "Population size: {0}\n\n".format(self.population_size)
#         
#         file_return += "Parameter count: {0}\n".format(self.param_count)
#         file_return += "Results count: {0}\n\n".format(self.result_count)
#         
#         file_return += "Minimum bounds: {0}\n".format(self.min_var)
#         file_return += "Maximum bounds: {0}\n\n".format(self.max_var)
#         
#         file_return += "p_mut: {0}\n".format(self.pmut)
#         file_return += "p_cross: {0}\n".format(self.pcross)
#         file_return += "eta_m: {0}\n".format(self.eta_m)
#         file_return += "eta_c: {0}\n\n".format(self.eta_c)
#         
#         file_return += "Seed: {0}\n".format(self.seed)
#         file_return += "Individuals: {0}".format(self.individuals)
#         
#         return file_return
        
    def evaluate_swarm(self, population):
        data = []
        
        for particle in range(len(population)):
            # Configure machine for the measurement
            self.interactor.set_ap(population[particle.pos_i])
            #data.append(self.interactor.get_ar())
            all_data = self.interactor.get_ar()
            #all_data = [i.mean for i in all_data] # Pull out just the means from the returned data
            data.append(all_data)
            
        #return [i[0] for i in data]
        return data
    

    def dump_fronts(self, fronts, generation):
        
        f = file("{0}/fronts.{1}".format(self.store_location, generation), "w")
        f.write("fronts = (\n")
        for i, front in enumerate(fronts):
            f.write("( # Front %d\n" % i)
            for ff in front:
                #f.write("    (%s, %s),\n" % (ff.x[:], ff[:]))
                f.write("    (%s, %s, %s),\n" % (ff.x[:], ff[:], tuple(ff.unc[:])))
                print "\n\n\n!!!\n{0}\n!!!\n\n\n".format(ff.unc[:])
            f.write("),\n")
        f.write(")\n")
        f.close()
        
        pass
    
    def pareto_remover(self,a,b):
        if all(a_i > b_i for (a_i,b_i) in zip(a,b)):
            return a
        if all(a_i < b_i for (a_i,b_i) in zip(a,b)):
            return b
        if all(a_i == b_i for (a_i,b_i) in zip(a,b)):
            return b
        else:
            return False
            
    def get_pareto_objectives(self, swarm):
        objectives = [particle[1] for particle in swarm]
        return objectives

    def pareto_test(self,a,b):
        if all(a_i > b_i for (a_i,b_i) in zip(a,b)):
            return False #this particle doesn't belong on the front
        else:
            return True
        
    def find_pareto_front(self,swarm):
        global pareto_front
        
        current_swarm = list(self.get_pareto_objectives(swarm))
        indices_to_delete = []
        
        for i in range(len(current_swarm)):
            for j in range(len(current_swarm)):
                #print 'compare', current_swarm[i], 'and', current_swarm[j]
                if i==j:
                    continue
                
                particle_to_remove = self.pareto_remover(current_swarm[i], current_swarm[j])
                if particle_to_remove == False:
                    #print 'do nothing'
                    continue
                
                else:
                    indices_to_delete.append(current_swarm.index(particle_to_remove))
                    #print 'remove', particle_to_remove
                
        indices_to_delete = sorted(set(indices_to_delete), reverse=True)
        for i in indices_to_delete:
            del swarm[i]
        pareto_front = list(swarm)

    def kernel_density_estimator(self, solution, current_swarm):
        global pareto_front
        pareto_front_positions = self.get_pareto_objectives(pareto_front)
        #print 'pareto front', pareto_front_positions
        kd_tree = spatial.KDTree(pareto_front_positions)
        nearest_neighbours = [pareto_front_positions[i] for i in kd_tree.query(solution, len(solution)+1)[1]]
        del nearest_neighbours[0]
        
        swarm_in_box = list(current_swarm)
        #print 'swarm in box', swarm_in_box
    
        for i in range(len(solution)):
            nearest_neighbour_coords = [row[i] for row in nearest_neighbours]
            coords = [row[i] for row in swarm_in_box]
            coord_boundaries = [min(nearest_neighbour_coords),max(nearest_neighbour_coords)]
    
            indices_to_remove = []
            for j in range(len(swarm_in_box)):
                if coords[j]<coord_boundaries[0] or coords[j]>coord_boundaries[1]:
                    indices_to_remove.append(j)
            
        indices_to_remove = sorted(set(indices_to_remove), reverse=True)
        for i in indices_to_remove:
            del swarm_in_box[i]
                    
        return len(swarm_in_box)
    
    def get_leader_roulette_wheel(self, current_swarm):
        global pareto_front
        if len(pareto_front) < len(pareto_front[0][1])+1:
            return []
        pareto_front_positions = self.get_pareto_objectives(pareto_front)
        current_swarm_objective_postions = [i.fit_i for i in current_swarm]
        fitness = [(1/(self.kernel_density_estimator(i, current_swarm_objective_postions)+1)) for i in pareto_front_positions]
        total_fit = sum(fitness)
        roulette_wheel = len(fitness) * [fitness[0]/total_fit]
        for f in range(1,len(fitness)):
            roulette_wheel[f] = roulette_wheel[f-1] + fitness[f]/total_fit
        return roulette_wheel
       
    def evaluate(self, swarm, initial_evaluation=False):
        
        objectives = self.evaluate_swarm(swarm)
        for particle in swarm:                
            particle.fit_i = objectives[particle] 
        
            #check is this is a personal best
            if initial_evaluation==False:
                if self.pareto_test(particle.fit_i,particle.fit_best_i) == True:
                    particle.pos_best_i = particle.position_i
                    particle.fit_best_i = particle.fit_i
                    
            if initial_evaluation==True:
                particle.fit_best_i = particle.fit_i
                particle.pos_best_i = particle.position_i 
    
    
    
    def optimise(self):
        
        global store_address
        global pareto_front
        global completed_address
        store_address = self.store_location

        # Make the save directory
        if not os.path.exists(self.store_location):
            os.makedirs(self.store_location)
        
        if self.add_current_to_individuals:
            current_ap = self.interactor.get_ap()
            self.individuals = list(self.individuals)
            self.individuals[0] = current_ap
    
        # initialize population
        swarm = []
        for i in range(0, self.swarm_size):
            swarm.append(Particle(self.param_count, self.min_var, self.max_var))
        
        self.evaluate(swarm, initial_evaluation=True)
        proposed_pareto = [[j.position_i,j.fit_i] for j in swarm]
        self.find_pareto_front(proposed_pareto)
        self.dump_fronts(pareto_front, 0)
        
        # for each generation
        for t in range(1,self.max_iter):
            
            leader_roullete_wheel = self.get_leader_roulette_wheel(swarm)
            for j in range(0, self.swarm_size):
                swarm[j].select_leader(leader_roullete_wheel)
                swarm[j].update_velocity()
                swarm[j].update_position()               
                self.evaluate(swarm)
            
            proposed_pareto = [[j.position_i,j.fit_i] for j in swarm]
            self.find_pareto_front(proposed_pareto)
            self.dump_fronts(pareto_front, t)
    
            # Signal progress
            print "generation %d" % t
            completed_generation = t
            self.progress_handler(float(t) / float(self.generations), t)
            while self.pause:
                self.progress_handler(float(t) / float(self.generations), t)
    
        print "DONE"
        #self.progress_handler(t+1)
        
class Particle:
    def __init__(self, num_parameter, par_min, par_max):
        self.position_i = [random.uniform(par_min[i],par_max[i]) for i in range(num_parameter)]                                                                     #particle position
        self.velocity_i = [random.uniform(par_min[i],par_max[i]) for i in range(num_parameter)]        #particle velocity
        self.pos_best_i = []                                                                     #particle's best position
        self.leader_i = []                                                                       #particle's leader
        self.fit_i = []                                                                          #particle fit 
        self.fit_best_i = [] 
        self.bounds = [par_min, par_max]
        #particle best fit

    #find particle's current fit
    

            
    # update new velocity
    def update_velocity(self):
        w = 0.4                      #inertia constant
        c1 = 2.0                    #cognitive parameter
        c2 = 2.0                    #social parameter
        
        for i in range(0, self.num_parameter):
            r1 = random.random()
            r2 = random.random()
            velocity_cognitive = c1 * r1 * (self.pos_best_i[i] - self.position_i[i])
            velocity_social = c2 * r2 * (self.leader_i[i] - self.position_i[i])
            self.velocity_i[i] = w*self.velocity_i[i] + velocity_cognitive + velocity_social
    
    # update new position using new velocity
    def update_position(self):
        
        for i in range(0,self.num_parameter):
            self.position_i[i]= self.position_i[i] + self.velocity_i[i]
            
            #adjust if particle goes above max bound
            if self.position_i[i] > self.bounds[1][i]:
                self.position_i[i] = self.bounds[1][i]
                self.velocity_i[i] = -1 * self.velocity_i[i]
                
            #adjust if particle goes below min bound
            if self.position_i[i] < self.bounds[0][i]:
                self.position_i[i] = self.bounds[0][i]
                self.velocity_i[i] = -1 * self.velocity_i[i]

    def select_leader(self, roulette_wheel):
        global pareto_front
        if len(pareto_front) < len(pareto_front[0][1]) +1:
            self.leader_i = random.choice(pareto_front)[0]
            return
        
        r = random.random()
        for i in range(len(pareto_front)):
            if r <= roulette_wheel[i]:
                self.leader_i = pareto_front[i][0]

class import_algo_frame(Tkinter.Frame):
    
    def __init__(self, parent):
        
        Tkinter.Frame.__init__(self, parent)
        
        self.parent = parent
        
        self.initUi()
    
    def initUi(self):
        #self.parent.title("NSGA-II Settings")
        self.add_current_to_individuals = Tkinter.BooleanVar(self)
        self.add_current_to_individuals.set(True)
        
        Tkinter.Label(self, text="Population size:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self)
        self.i0.grid(row=0, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Max. generations:").grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self)
        self.i1.grid(row=1, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Mutation probability:").grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self)
        self.i2.grid(row=2, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Crossover probability:").grid(row=3, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self)
        self.i3.grid(row=3, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Eta_m:").grid(row=4, column=0, sticky=Tkinter.E)
        self.i4 = Tkinter.Entry(self)
        self.i4.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Eta_c:").grid(row=5, column=0, sticky=Tkinter.E)
        self.i5 = Tkinter.Entry(self)
        self.i5.grid(row=5, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Seed:").grid(row=6, column=0, sticky=Tkinter.E)
        self.i6 = Tkinter.Entry(self)
        self.i6.grid(row=6, column=1, sticky=Tkinter.E+Tkinter.W)
        self.i6.insert(0, time.time())
        
        Tkinter.Label(self, text="Parameter count:").grid(row=7, column=0, sticky=Tkinter.E)
        self.i7 = Tkinter.Entry(self)
        self.i7.grid(row=7, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Result count:").grid(row=8, column=0, sticky=Tkinter.E)
        self.i8 = Tkinter.Entry(self)
        self.i8.grid(row=8, column=1, sticky=Tkinter.E+Tkinter.W)
        
        self.c0 = Tkinter.Checkbutton(self, text="Use current machine state", variable=self.add_current_to_individuals)
        self.c0.grid(row=9, column=1)
        
        Tkinter.Label(self, text="Recommended:\nMutation probability: 0.1 / (number of decision variables)\nCrossover probability: 0.9\nEta_m: 20\nEta_c: 20\nSeed: Any int or float (default is seconds since system epoch)", justify=Tkinter.LEFT).grid(row=10, column=0, columnspan=2, sticky=Tkinter.W)
        
        self.i0.insert(0, "10")
        self.i1.insert(0, "10")
        self.i2.insert(0, "0.033333")
        self.i3.insert(0, "0.9")
        self.i4.insert(0, "20")
        self.i5.insert(0, "20")
        self.i7.insert(0, "3")
        self.i8.insert(0, "2")
        
    
    def get_dict(self):
        
        good_data = True
        setup = {}
        
        try:
            setup['pop_size'] = int(self.i0.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Population size\": \"{0}\", could not be converted to an int".format(self.i0.get()))
            good_data = False
        
        try:
            setup['max_gen'] = int(self.i1.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Max. generations\": \"{0}\", could not be converted to an int".format(self.i1.get()))
            good_data = False
        
        try:
            setup['pmut'] = float(self.i2.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Mutation probability\": \"{0}\", could not be converted to a float".format(self.i2.get()))
            good_data = False
        
        try:
            setup['pcross'] = float(self.i3.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Crossover probability\": \"{0}\", could not be converted to a float".format(self.i3.get()))
            good_data = False
        
        try:
            setup['eta_m'] = float(self.i4.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Eta_m\": \"{0}\", could not be converted to a float".format(self.i4.get()))
            good_data = False
        
        try:
            setup['eta_c'] = float(self.i5.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Eta_c\": \"{0}\", could not be converted to a float".format(self.i5.get()))
            good_data = False
        
        try:
            setup['seed'] = float(self.i6.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Seed\": \"{0}\", could not be converted to a float".format(self.i6.get()))
            good_data = False
        
        try:
            setup['param_count'] = int(self.i7.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Parameter count\": \"{0}\", could not be converted to an int".format(self.i7.get()))
            good_data = False
        
        try:
            setup['result_count'] = int(self.i8.get())
        except:
            tkMessageBox.showerror("NSGA-II settings error", "The value for \"Result count\": \"{0}\", could not be converted to an int".format(self.i8.get()))
            good_data = False
        
        if self.add_current_to_individuals.get() == 0:
            setup['add_current_to_individuals'] = False
        elif self.add_current_to_individuals.get() == 1:
            setup['add_current_to_individuals'] = True
        
        if good_data:
            return setup
        else:
            return "error"
        
        
    



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
        for i in range(completed_generation + 1):
            file_names.append("{0}/fronts.{1}".format(store_address, i))
        
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
        
        self.parent.title("NSGA-II Results")
        
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
        #for i in range(algo_settings_dict['max_gen']):
        for i in range(completed_generation+1):
            file_names.append("{0}/fronts.{1}".format(store_address, i))
        
        
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
        
        for widget in self.winfo_children():
            widget.destroy()
        
        fig = Figure(figsize=(5, 5), dpi=100)
        a = fig.add_subplot(111)
        fig.subplots_adjust(left=0.15)
        #a.plot(range(10), [i**2 for i in range(10)])
        
        file_names = []
        #for i in range(algo_settings_dict['max_gen']):
        for i in range(completed_generation+1):
            file_names.append("{0}/fronts.{1}".format(store_address, i))
        
        plot.plot_pareto_fronts_interactive(file_names, a, self.axis_labels, None, None, self.parent.view_mode.get())
        
        canvas = FigureCanvasTkAgg(fig, self)
        canvas.mpl_connect('pick_event', self.parent.on_pick)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)
        
        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)
