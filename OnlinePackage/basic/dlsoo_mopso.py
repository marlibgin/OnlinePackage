'''
MULTI-OBJECTIVE PARTICLE SWARM OPTIMISER for use in the DLS OnlineOptimiser package. 
Created on 7 Jul 2017
@author: James Rogers
'''

#-----------------------------------------------------------------IMPORT LIBRARIES-----------------------------------------------------------------#

import random
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

#------------------------------------------------------GLOBAL VARIABLES AND USEFUL FUNCTIONS-------------------------------------------------------#

store_address = None                            #directory in which output data will be stored
completed_iteration = None                      #number of completed iterations
completed_percentage = 0.0
pareto_front = ()                               #current pareto-front with the format (((param1,param2,...),(obj1,obj2,...),(err1,err2,...)),...)

# colour display codes
ansi_red = "\x1B[31m"
ansi_normal = "\x1B[0m"

def nothing_function(data):
    pass

#----------------------------------------------------------------OPTIMISER CLASS-------------------------------------------------------------------#

class optimiser:
    
    def __init__(self, settings_dict, interactor, store_location, a_min_var, a_max_var, progress_handler=None):
        
        self.interactor = interactor                                         #interactor with dls_optimiser_util.py
        self.store_location = store_location                                 #location for output files
        self.swarm_size = settings_dict['swarm_size']                        #number of particles in swarm
        self.max_iter = settings_dict['max_iter']                            #number of iterations of algorithm
        self.param_count = settings_dict['param_count']                      #number of parameters being varied
        self.result_count = settings_dict['result_count']                    #number of objectives being measured
        self.min_var = a_min_var                                             #minimum values of parameters
        self.max_var = a_max_var                                             #minimum values of parameters
        self.inertia = settings_dict['inertia']                              #inertia of particles in swarm
        self.social_param = settings_dict['social_param']                    #social parameter for particles in swarm
        self.cognitive_param = settings_dict['cognitive_param']              #cognitive parameter for particles in swarm
        
        if progress_handler == None:
            progress_handler = nothing_function
        
        self.progress_handler = progress_handler
        
        self.pause = False
        print "interactor.param_var_groups: {0}".format(interactor.param_var_groups)
        print "interactor.measurement_vars: {0}".format(interactor.measurement_vars)
    
    def save_details_file(self):
        """
        Function writes a file containing details of algorithm run
        """       
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
    
    
    def evaluate_swarm(self, swarm):
        """
        Function measures the objective functions for an entire swarm.
        
        Args:
            swarm: list of Particle instances ready for measurement.
        
        Returns:
            results: list of calculated results for each Particle instance
            errors: list of calculated errors for each Particle instance measurement
        """
        
        global completed_percentage
        global completed_iteration
        
        percentage_interval = (1./self.max_iter)/self.swarm_size                  #calculate percentage update per measurement
        results = []
        errors = []
        
        for i in range(len(swarm)):
            
            self.interactor.set_ap(swarm[i].position_i)                           #configure machine for measurement
            all_data = self.interactor.get_ar()                                   #perform measurement 
            
            all_results = [i.mean for i in all_data]                              #retrieve mean from measurement 
            all_errors = [i.err for i in all_data]                                #retrieve error from measurement 
            
            results.append(all_results)
            errors.append(all_errors)
            
            completed_percentage += percentage_interval                           #update percentage bar on progress plot
            print completed_percentage,'%'
            self.progress_handler(completed_percentage, completed_iteration)
        
        while self.pause:                                                         #keep update bar if algorithm paused
                self.progress_handler(completed_percentage, completed_iteration)
            
        return results, errors
    

    def dump_fronts(self, fronts, iteration):
        """
        Function dumps data of current front in file in output directory e.g. fronts.1 will contain the first front calculated.
        
        Args:
            fronts: pareto-front to be dumped
            iteration: current iteration number
        Returns:
            None
        """
        f = file("{0}/fronts.{1}".format(self.store_location, iteration), "w")             #open file
        f.write("fronts = ((\n")
        for i, data in enumerate(fronts):
            f.write("    ({0}, {1}, {2}),\n".format(data[0], tuple(data[1]), data[2]))     #insert each solution in front
        f.write("),)\n")
        f.close()                                                                          #close file
        
        pass

    
    def pareto_remover(self,a,b):
        """
        Function determines which of two points is the dominant in objective space.
        
        Args:
            a: list of objective values [obj1,obj2,...]
            b: list of objective values [obj1,obj2,...]
            
        Returns:
            Function will return the point that dominates the other. If neither dominates, return is False.
        """
        if all(a_i > b_i for (a_i,b_i) in zip(a,b)):         #does a dominate b?
            return a
        if all(a_i < b_i for (a_i,b_i) in zip(a,b)):         #does b dominate b?
            return b
        if all(a_i == b_i for (a_i,b_i) in zip(a,b)):        #are the points the same?
            return b
        else:
            return False
            
    def get_pareto_objectives(self, swarm):
        """
        Returns a list of objectives from front like list
        
        Args:
            swarm: list of solutions in the format (((param1,param2,...),(obj1,obj2,...),(err1,err2,...)),...).
            
        Returns:
            list of objectives in the format [(obj1,obj2,...),(obj1,obj2,...),...]
        """
        objectives = [particle[1] for particle in swarm]
        return objectives


    def pareto_test(self,a,b):
        """
        Determines whether a solution should remain in a pareto front.
        
        Args:
            a: list of objective values [obj1,obj2,...].
            b: list of objective values [obj1,obj2,...].
            
        Returns:
            False if a dominates b.
            True if both a and b are non-dominant.
        """
        if all(a_i > b_i for (a_i,b_i) in zip(a,b)):    #does a dominate b for all objectives?
            return False 
        else:
            return True
        
        
    def find_pareto_front(self,swarm):
        """
        For a given swarm of solutions, this function will determine the non-dominant set and update the pareto-front.
        
        Args:
            swarm: set of solutions in the form (((param1,param2,...),(obj1,obj2,...),(err1,err2,...)),...).
        
        Returns:
            None, but updates the global variable pareto_front with the new non-dominant solutions.
        """
        global pareto_front        
        current_swarm = list(self.get_pareto_objectives(swarm))
        indices_to_delete = []
        
        for i in range(len(current_swarm)):                                                      #cycle through swarm and compare objectives
            for j in range(len(current_swarm)):
                
                if i==j:                                                                         #no need to compare solution with itself 
                    continue
                
                particle_to_remove = self.pareto_remover(current_swarm[i], current_swarm[j])     #determine which solution is dominant 
                
                if particle_to_remove == False:                                                  #if neither are dominant, leave both in front
                    continue                
                else:
                    indices_to_delete.append(current_swarm.index(particle_to_remove))            #store index of solution if it is dominant
                
        indices_to_delete = sorted(set(indices_to_delete), reverse=True)
        for i in indices_to_delete:                                                              #remove dominating solutions 
            del swarm[i]
        pareto_front = list(swarm)                                                               #update global pareto_front


    def density_estimator(self, solution, current_swarm):
        """
        This function counts the number of particles that are near a solution in the pareto front.
        
        Args:
            solution: solution in pareto front of the form (obj1,obj2,...)
            current_swarm: list of solutions for current swarm of the form ((obj1,obj2,...),(obj1,obj2,...),...)
            
        Returns:
            Number of particles near the solution in the pareto-front.
        """
        global pareto_front 
        pareto_front_obj = self.get_pareto_objectives(pareto_front)                                         #obtain list of objectives of pareto front                                    
        kd_tree = spatial.KDTree(pareto_front_obj)                                                          #form KDTree of all other particles in pareto-front
        
        nearest_neighbours = [pareto_front_obj[i] for i in kd_tree.query(solution, len(solution)+1)[1]]     #find dim(solution) +1 nearest neighbours to solution 
        del nearest_neighbours[0]                                                                           #ignore closest as this is solution itself
        
        swarm_in_box = list(current_swarm)    
        for i in range(len(solution)):                                                                      #define hyper-cuboid with closest neighbours at vertices
            nearest_neighbour_coords = [row[i] for row in nearest_neighbours]
            coords = [row[i] for row in swarm_in_box]
            coord_boundaries = [min(nearest_neighbour_coords),max(nearest_neighbour_coords)]
    
            indices_to_remove = []
            for j in range(len(swarm_in_box)):
                if coords[j]<coord_boundaries[0] or coords[j]>coord_boundaries[1]:                          #find particle indices that lie outside hyper-cuboid
                    indices_to_remove.append(j)
            
        indices_to_remove = sorted(set(indices_to_remove), reverse=True)
        for i in indices_to_remove:
            del swarm_in_box[i]                                                                             #obtain list of particles that are within bounds of hyper-cuboid                                  
                    
        return len(swarm_in_box)                                                                            #return number of particles inside hyper-cuboid 
    
    
    def get_leader_roulette_wheel(self, current_swarm):
        """
        Function that produces a roulette wheel selection list for solutions in pareto-front
        
        Args:
            current_swarm: list of Particle instances.
            
        Returns;
            roulette_wheel: list of roulette wheel probabilities inversely proportional to number of particles near each particle in the pareto-front.
        """
        global pareto_front

        if len(pareto_front) < len(pareto_front[0][1])+1:                                                                   #no roulette wheel possible if not enough solutions in pareto-front
            return []
        
        pareto_front_positions = self.get_pareto_objectives(pareto_front)                                                   #get pareto-front solutions
        current_swarm_objectives = [i.fit_i for i in current_swarm]                                                         #get swarm solutions 
        
        fitness = [(1/(self.density_estimator(i, current_swarm_objectives)+1)) for i in pareto_front_positions]             #calculate inverse of density  
                   
        total_fit = sum(fitness)   
        roulette_wheel = len(fitness) * [fitness[0]/(total_fit+1)]                                                          #define roulette wheel              
        
        for f in range(1,len(fitness)):
            roulette_wheel[f] = roulette_wheel[f-1] + fitness[f]/(total_fit+1)                                              #calculate cumulative probabilities

        return roulette_wheel
       
       
    def evaluate(self, swarm, initial_evaluation=False):
        """
        Function evaluates objectives for the swarm and updates best positions for each particle instance
        
        Args:
            swarm: list of Particle instances
            initial_evaluation: this should be True if this is the first iteration.
        
        Returns:
            None, but updates all particle best locations in objective space for next iteration.
        """
        
        objectives, errors = self.evaluate_swarm(swarm)                                    #obtain objective measurements and errors for all particles.
        for i in range(len(swarm)):                
            swarm[i].fit_i = objectives[i]                                                 #update current objective fit.
            swarm[i].error = errors[i]                                                     #update current objective error.
        
            if initial_evaluation==False:
                if self.pareto_test(swarm[i].fit_i,swarm[i].fit_best_i) == True:           #check if this objective fit is a personal best for the particle.
                    swarm[i].pos_best_i = swarm[i].position_i
                    swarm[i].fit_best_i = swarm[i].fit_i
                    
            if initial_evaluation==True:                                                   #for the first iteration, the fit will be the personal best. 
                swarm[i].fit_best_i = swarm[i].fit_i
                swarm[i].pos_best_i = swarm[i].position_i
    
    
    
    def optimise(self):
        """
        This function runs the optimisation algorithm. It initialises the swarm and then takes successive measurements whilst
        updating the loaction of the swarm. It also updates the pareto-front archive after each iteration.
        
        Args:
            None
            
        Returns:
            None, but the pareto-front archive will have been updated with the non-dominating front.        
        """
        
        global store_address
        global pareto_front
        global completed_iteration
        store_address = self.store_location

        if not os.path.exists(self.store_location):                                               #make save directory
            os.makedirs(self.store_location)
        
#         if self.add_current_to_individuals:
#             current_ap = self.interactor.get_ap()
#             self.individuals = list(self.individuals)
#             self.individuals[0] = current_ap
    
        swarm = []
        for i in range(0, self.swarm_size):                                                       #initialise the swarm 
            swarm.append(Particle(self.param_count, self.min_var, self.max_var))
        
        completed_iteration = 0
        self.evaluate(swarm, initial_evaluation=True)   
        proposed_pareto = [[j.position_i,j.fit_i,j.error] for j in swarm]                         #define the front for sorting 
        self.find_pareto_front(proposed_pareto)                                                   #find the non-dominating set
        front_to_dump = tuple(list(pareto_front))                                                 #dump new front in file
        self.dump_fronts(front_to_dump, 0)
        
        for t in range(1,self.max_iter):                                                          #begin iteration 
            leader_roullete_wheel = self.get_leader_roulette_wheel(swarm)                         #calculate leader roulette wheel for the swarm
            for j in range(0, self.swarm_size):                                                   #for every particle:                                               
                swarm[j].select_leader(leader_roullete_wheel)                                     #select leader
                swarm[j].update_velocity(self.inertia, self.social_param, self.cognitive_param)   #update velocity   
                swarm[j].update_position()                                                        #update position
             
            self.evaluate(swarm)                                                                  #evaluate new positions            
            proposed_pareto = [[j.position_i,j.fit_i,j.error] for j in swarm] + pareto_front      #define front for sorting
            self.find_pareto_front(proposed_pareto)                                               #find the non-dominating set
            front_to_dump = list(pareto_front)                                                    #dump new front in file
            self.dump_fronts(front_to_dump, t)
            
            completed_iteration = t                                                               #track iteration number
            
        print "OPTIMISATION COMPLETE"


#----------------------------------------------------------------PARTICLE CLASS--------------------------------------------------------------------#
        
class Particle:
    
    def __init__(self, num_parameter, par_min, par_max):
        
        self.position_i = tuple([random.uniform(par_min[i],par_max[i]) for i in range(num_parameter)])        #particle's position
        self.velocity_i = tuple([random.uniform(par_min[i],par_max[i]) for i in range(num_parameter)])        #particle's velocity
        self.pos_best_i = ()                                                                                  #particle's best position
        self.leader_i = ()                                                                                    #particle's leader
        self.fit_i = ()                                                                                       #particle's fit 
        self.fit_best_i = ()                                                                                  #particle's best fit
        self.bounds = (par_min, par_max)                                                                      #particle's parameter bounds  
        self.error = ()                                                                                       #particle's error in fit
             
             
    def update_velocity(self, inertia, social_param, cog_param):
        """
        Function updates particle velocity according to particle swarm velocity equation.
        
        Args:
            inertia: inertia parameter gives particles mass (float type).
            social_param: social parameter give particles an attraction to swarm's best locations (float type).
            cog_param: cognitive parameter gives a particle an attraction to its own best location.
        
        Returns:
            None, but updates the particle's velocity attribute.
        """
        new_velocity = list(self.velocity_i)
        
        for i in range(0, len(self.bounds[0])):                                                        #new velocity in each parameter dimension 
            
            r1 = random.random()                                                                       #random numbers between [-1,1] for random-walk nature of code
            r2 = random.random()
            
            velocity_cognitive = cog_param * r1 * (self.pos_best_i[i] - self.position_i[i])            #calculate cognitive velocity term
            velocity_social = social_param * r2 * (self.leader_i[i] - self.position_i[i])              #calculate social velocity term
            
            new_velocity[i] = inertia*new_velocity[i] + velocity_cognitive + velocity_social           #calculate new velocity
            
        self.velocity_i = tuple(new_velocity)                                                          #update particle  velocity attribute
    

    def update_position(self):
        """
        Function updates particle position according to particle swarm position equation.
        
        Args:
            None
        
        Returns:
            None, but updates the particle's position.
        """
        new_position = list(self.position_i)
        new_velocity = list(self.velocity_i)
        for i in range(0,len(self.bounds[0])):                                                         #new position in each parameter dimension
            new_position[i]= new_position[i] + self.velocity_i[i]                                      #calculate new position                                     
            
            if new_position[i] > self.bounds[1][i]:                                                    #reflect if particle goes beyond upper bounds
                new_position[i] = self.bounds[1][i]
                new_velocity[i] = -1 * new_velocity[i]
                
            if new_position[i] < self.bounds[0][i]:                                                    #reflect if particle goes below lower bounds
                new_position[i] = self.bounds[0][i]
                new_velocity[i] = -1 * new_velocity[i]
                
        self.velocity_i = tuple(new_velocity)                                                          #update particle velocity attribute                             
        self.position_i = tuple(new_position)                                                          #update particle position attribute   
            

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
