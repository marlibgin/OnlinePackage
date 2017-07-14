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
completed_iteration = None
pareto_front = ()

# colour display codes
ansi_red = "\x1B[31m"
ansi_normal = "\x1B[0m"

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
        
#         if settings_dict['seed'] == None:
#             seed = time.time()
#         
#         self.seed = settings_dict['seed']
        
        self.pause = False
        print "interactor.param_var_groups: {0}".format(interactor.param_var_groups)
        print "interactor.measurement_vars: {0}".format(interactor.measurement_vars)
    
    def save_details_file(self):
         
        file_return = ""
         
        file_return += "MOPSO algorithm\n"
        file_return += "=================\n\n"
        file_return += "Iterations: {0}\n".format(self.max_iter)
        file_return += "Swarm size: {0}\n\n".format(self.swarm_size)
         
        file_return += "Parameter count: {0}\n".format(self.param_count)
        file_return += "Results count: {0}\n\n".format(self.result_count)
         
        file_return += "Minimum bounds: {0}\n".format(self.min_var)
        file_return += "Maximum bounds: {0}\n\n".format(self.max_var)
         
        file_return += "Particle Inertia: {0}\n".format(self.inertia)
        file_return += "Social Parameter: {0}\n".format(self.social_param)
        file_return += "Cognitive Parameter: {0}\n".format(self.cognitive_param)
         
         
        return file_return
        
    def evaluate_swarm(self, population):
        results = []
        errors = []
        #print 'population :', population
        #print 'example :', dir(population[0])
        for i in range(len(population)):
            #print 'particle parameters: ', population[i].position_i
            # Configure machine for the measurement
            self.interactor.set_ap(population[i].position_i)
            #data.append(self.interactor.get_ar())
            all_data = self.interactor.get_ar()
            all_results = [i.mean for i in all_data] # Pull out just the means from the returned data
            all_errors = [i.err for i in all_data]
            results.append(all_results)
            errors.append(all_errors)
            
        #return [i[0] for i in data]
        #print 'data', data
        return results, errors
    

    def dump_fronts(self, fronts, generation):
        #print 'front to dump: ',fronts
        f = file("{0}/fronts.{1}".format(self.store_location, generation), "w")
        f.write("fronts = ((\n")
        for i, data in enumerate(fronts):
            #f.write("    (%s, %s),\n" % (ff.x[:], ff[:]))
            f.write("    ({0}, {1}, {2}),\n".format(data[0], tuple(data[1]), data[2]))
            #print "\n\n\n!!!\n{0}\n!!!\n\n\n".format(ff.unc[:])
        f.write("),)\n")
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
        print 'pareto length is ',len(pareto_front)
        print 'swarm length is ', len(current_swarm)
        if len(pareto_front) < len(pareto_front[0][1])+1:
            return []
        pareto_front_positions = self.get_pareto_objectives(pareto_front)
        current_swarm_objective_postions = [i.fit_i for i in current_swarm]
        fitness = [(1/(self.kernel_density_estimator(i, current_swarm_objective_postions)+1)) for i in pareto_front_positions]
        total_fit = sum(fitness)
        roulette_wheel = len(fitness) * [fitness[0]/(total_fit+1)]
        for f in range(1,len(fitness)):
            roulette_wheel[f] = roulette_wheel[f-1] + fitness[f]/(total_fit+1)
        print 'roulette wheel', roulette_wheel
        return roulette_wheel
       
    def evaluate(self, swarm, initial_evaluation=False):
        
        objectives, errors = self.evaluate_swarm(swarm)
        for i in range(len(swarm)):                
            swarm[i].fit_i = objectives[i] 
            swarm[i].error = errors[i]
        
            #check is this is a personal best
            if initial_evaluation==False:
                if self.pareto_test(swarm[i].fit_i,swarm[i].fit_best_i) == True:
                    swarm[i].pos_best_i = swarm[i].position_i
                    swarm[i].fit_best_i = swarm[i].fit_i
                    
            if initial_evaluation==True:
                swarm[i].fit_best_i = swarm[i].fit_i
                swarm[i].pos_best_i = swarm[i].position_i
    
    
    
    def optimise(self):
        
        global store_address
        global pareto_front
        global completed_iteration
        store_address = self.store_location

        # Make the save directory
        if not os.path.exists(self.store_location):
            os.makedirs(self.store_location)
        
#         if self.add_current_to_individuals:
#             current_ap = self.interactor.get_ap()
#             self.individuals = list(self.individuals)
#             self.individuals[0] = current_ap
    
        # initialise population
        swarm = []
        for i in range(0, self.swarm_size):
            swarm.append(Particle(self.param_count, self.min_var, self.max_var))
            #print 'first position = ', swarm[i].position_i
        
        self.evaluate(swarm, initial_evaluation=True)
        proposed_pareto = [[j.position_i,j.fit_i,j.error] for j in swarm]
        print 'proposed pareto = ',proposed_pareto
        self.find_pareto_front(proposed_pareto)
        print 'new pareto is ',pareto_front
        front_to_dump = tuple(list(pareto_front))
        self.dump_fronts(front_to_dump, 0)
        
        # for each generation
        for t in range(1,self.max_iter):
            print 'iteration = ',t
            leader_roullete_wheel = self.get_leader_roulette_wheel(swarm)
            for j in range(0, self.swarm_size):
                swarm[j].select_leader(leader_roullete_wheel)
                swarm[j].update_velocity()
                swarm[j].update_position()
                self.evaluate(swarm)
            
            proposed_pareto = [[j.position_i,j.fit_i,j.error] for j in swarm] + pareto_front
            self.find_pareto_front(proposed_pareto)
            front_to_dump = list(pareto_front)
            self.dump_fronts(front_to_dump, t)
    
            # Signal progress
            print "generation %d" % t
            completed_iteration = t
            self.progress_handler(float(t) / float(self.max_iter), t)
            while self.pause:
                self.progress_handler(float(t) / float(self.max_iter), t)
    
        print "DONE"
        #self.progress_handler(t+1)
        
class Particle:
    def __init__(self, num_parameter, par_min, par_max):
        self.position_i = tuple([random.uniform(par_min[i],par_max[i]) for i in range(num_parameter)])                                                                     #particle position
        self.velocity_i = tuple([random.uniform(par_min[i],par_max[i]) for i in range(num_parameter)])        #particle velocity
        self.pos_best_i = ()                                                                     #particle's best position
        self.leader_i = ()                                                                       #particle's leader
        self.fit_i = ()                                                                          #particle fit 
        self.fit_best_i = () 
        self.bounds = (par_min, par_max)
        self.error = ()
        #particle best fit

    #find particle's current fit
    

            
    # update new velocity
    def update_velocity(self):
        w = 0.4                      #inertia constant
        c1 = 2.0                    #cognitive parameter
        c2 = 2.0                    #social parameter
        new_velocity = list(self.velocity_i)
        print 'parameters = ',len(self.bounds[0])
        print 'social = ',len(self.leader_i)
        for i in range(0, len(self.bounds[0])):
            print 'i = ',i
            r1 = random.random()
            r2 = random.random()
            
            velocity_cognitive = c1 * r1 * (self.pos_best_i[i] - self.position_i[i])
            velocity_social = c2 * r2 * (self.leader_i[i] - self.position_i[i])
            new_velocity[i] = w*new_velocity[i] + velocity_cognitive + velocity_social
        self.velocity_i = tuple(new_velocity)
    
    # update new position using new velocity
    def update_position(self):
        new_position = list(self.position_i)
        new_velocity = list(self.velocity_i)
        for i in range(0,len(self.bounds[0])):
            new_position[i]= new_position[i] + self.velocity_i[i]
            
            #adjust if particle goes above max bound
            if new_position[i] > self.bounds[1][i]:
                new_position[i] = self.bounds[1][i]
                new_velocity[i] = -1 * new_velocity[i]
                
            #adjust if particle goes below min bound
            if new_position[i] < self.bounds[0][i]:
                new_position[i] = self.bounds[0][i]
                new_velocity[i] = -1 * new_velocity[i]
        self.velocity_i = tuple(new_velocity)
        self.position_i = tuple(new_position)
            

    def select_leader(self, roulette_wheel):
        global pareto_front
        if len(pareto_front) < len(pareto_front[0][1]) +1:
            self.leader_i = random.choice(pareto_front)[0]
            print 'new leader is ',self.leader_i
            return
        
        r = random.random()
        for i in range(len(pareto_front)):
            if r <= roulette_wheel[i]:
                self.leader_i = pareto_front[i][0]
            else:
                self.leader_i = random.choice(pareto_front)[0]

class import_algo_frame(Tkinter.Frame):
    
    def __init__(self, parent):
        
        Tkinter.Frame.__init__(self, parent)
        
        self.parent = parent
        
        self.initUi()
    
    def initUi(self):
        #self.parent.title("NSGA-II Settings")
        self.add_current_to_individuals = Tkinter.BooleanVar(self)
        self.add_current_to_individuals.set(True)
        
        Tkinter.Label(self, text="Swarm size:").grid(row=0, column=0, sticky=Tkinter.E)
        self.i0 = Tkinter.Entry(self)
        self.i0.grid(row=0, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Max. iterations:").grid(row=1, column=0, sticky=Tkinter.E)
        self.i1 = Tkinter.Entry(self)
        self.i1.grid(row=1, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Particle Inertia:").grid(row=2, column=0, sticky=Tkinter.E)
        self.i2 = Tkinter.Entry(self)
        self.i2.grid(row=2, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Social Parameter:").grid(row=3, column=0, sticky=Tkinter.E)
        self.i3 = Tkinter.Entry(self)
        self.i3.grid(row=3, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Cognitive Parameter:").grid(row=4, column=0, sticky=Tkinter.E)
        self.i4 = Tkinter.Entry(self)
        self.i4.grid(row=4, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Parameter count:").grid(row=5, column=0, sticky=Tkinter.E)
        self.i5 = Tkinter.Entry(self)
        self.i5.grid(row=5, column=1, sticky=Tkinter.E+Tkinter.W)
        
        Tkinter.Label(self, text="Result count:").grid(row=6, column=0, sticky=Tkinter.E)
        self.i6 = Tkinter.Entry(self)
        self.i6.grid(row=6, column=1, sticky=Tkinter.E+Tkinter.W)
        
        #self.c0 = Tkinter.Checkbutton(self, text="Use current machine state", variable=self.add_current_to_individuals)
        #self.c0.grid(row=9, column=1)
        
        Tkinter.Label(self, text="Recommended:\nSwarm Size: 15\nMax. Iterations: 10\nParticle Inertia: 0.4\nSocial Parameter: 2.0\nCognitive Parameter: 2.0", justify=Tkinter.LEFT).grid(row=7, column=0, columnspan=2, sticky=Tkinter.W)
        
        self.i0.insert(0, "15")
        self.i1.insert(0, "4")
        self.i2.insert(0, "0.4")
        self.i3.insert(0, "2.0")
        self.i4.insert(0, "2.0")
        self.i5.insert(0, "3")
        self.i6.insert(0, "2")
        
    
    def get_dict(self):
        
        good_data = True
        setup = {}
        
        try:
            setup['swarm_size'] = int(self.i0.get())
        except:
            tkMessageBox.showerror("MOPSO settings error", "The value for \"Swarm Size\": \"{0}\", could not be converted to an int".format(self.i0.get()))
            good_data = False
        
        try:
            setup['max_iter'] = int(self.i1.get())
        except:
            tkMessageBox.showerror("MOPSO settings error", "The value for \"Max. Iterations\": \"{0}\", could not be converted to an int".format(self.i1.get()))
            good_data = False
        
        try:
            setup['inertia'] = float(self.i2.get())
        except:
            tkMessageBox.showerror("MOPSO settings error", "The value for \"Particle Inertia\": \"{0}\", could not be converted to a float".format(self.i2.get()))
            good_data = False
        
        try:
            setup['social_param'] = float(self.i3.get())
        except:
            tkMessageBox.showerror("MOPSO settings error", "The value for \"Social Parameter\": \"{0}\", could not be converted to a float".format(self.i3.get()))
            good_data = False
        
        try:
            setup['cognitive_param'] = float(self.i4.get())
        except:
            tkMessageBox.showerror("MOPSO settings error", "The value for \"Cognitive Parameter\": \"{0}\", could not be converted to a float".format(self.i4.get()))
            good_data = False
        
        try:
            setup['param_count'] = int(self.i5.get())
        except:
            tkMessageBox.showerror("MOPSO settings error", "The value for \"Parameter count\": \"{0}\", could not be converted to an int".format(self.i7.get()))
            good_data = False
        
        try:
            setup['result_count'] = int(self.i6.get())
        except:
            tkMessageBox.showerror("MOPSO settings error", "The value for \"Result count\": \"{0}\", could not be converted to an int".format(self.i8.get()))
            good_data = False
        
#         if self.add_current_to_individuals.get() == 0:
#             setup['add_current_to_individuals'] = False
#         elif self.add_current_to_individuals.get() == 1:
#             setup['add_current_to_individuals'] = True
        
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
        global completed_iteration
        
        self.a.clear()
        
        file_names = []
        for i in range(completed_iteration + 1):
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
        global completed_iteration
        
        self.parent.title("MOPSO Results")
        
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
        for i in range(completed_iteration+1):
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
        for i in range(completed_iteration+1):
            file_names.append("{0}/fronts.{1}".format(store_address, i))
        
        plot.plot_pareto_fronts_interactive(file_names, a, self.axis_labels, None, None, self.parent.view_mode.get())
        
        canvas = FigureCanvasTkAgg(fig, self)
        canvas.mpl_connect('pick_event', self.parent.on_pick)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)
        
        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)