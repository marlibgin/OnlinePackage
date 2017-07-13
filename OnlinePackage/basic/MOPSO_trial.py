'''
Created on 7 Jul 2017

@author: James Rogers
'''
from __future__ import division

import sys
import random
import math
from scipy import spatial
from matplotlib import pyplot as plt

#-----------------------------EXTERNAL ARCHIVE---------------------------------#

pareto_front = []
pareto_history = []
swarm_history = []

#----------------------------OBJECTIVE FUNCTION--------------------------------#

#objectives to minimise, in this case a Kursawe function:

def kursawe_test_objective_function(x):
    f0 = 0
    for i in range(2):
        f0 = f0 + -10 * math.exp(-0.2 * math.sqrt(x[i] ** 2 + x[i+1] ** 2))
    f1 = 0
    for i in range(3):
        f1 = f1 + abs(x[i]) ** 0.8 + 5 * math.sin(x[i] ** 3)
    return [f0,f1]

def schaffer_test_objective_function(x):
    f0 = x[0]**2
    f1 = (x[0]-2)**2
    return [f0,f1]

#----------------------------PARETO INFO EXTRACTION----------------------------#

def get_pareto_parameters(swarm):
    parameters = [particle[0] for particle in swarm]
    return parameters

def get_pareto_objectives(swarm):
    objectives = [particle[1] for particle in swarm]
    return objectives


#---------------------------------DOMINATES------------------------------------#
def pareto_remover(a,b):
    if all(a_i > b_i for (a_i,b_i) in zip(a,b)):
        return a
    if all(a_i < b_i for (a_i,b_i) in zip(a,b)):
        return b
    if all(a_i == b_i for (a_i,b_i) in zip(a,b)):
        return b
    else:
        return False


def pareto_test(a,b):
    if all(a_i > b_i for (a_i,b_i) in zip(a,b)):
        return False #this particle doesn't belong on the front
    else:
        return True
    
def find_pareto_front(swarm):
    global pareto_front
    
    current_swarm = list(get_pareto_objectives(swarm))
    indices_to_delete = []
    
    for i in range(len(current_swarm)):
        for j in range(len(current_swarm)):
            #print 'compare', current_swarm[i], 'and', current_swarm[j]
            if i==j:
                continue
            
            particle_to_remove = pareto_remover(current_swarm[i], current_swarm[j])
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


#------------------------------DENSITY MEASURE---------------------------------#

def kernel_density_estimator(solution, current_swarm):
    global pareto_front
    pareto_front_positions = get_pareto_objectives(pareto_front)
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

#-----------------------------LEADER SELECTION---------------------------------#
def get_leader_roulette_wheel(current_swarm):
    global pareto_front
    if len(pareto_front) < len(pareto_front[0][1])+1:
        return []
    pareto_front_positions = get_pareto_objectives(pareto_front)
    current_swarm_objective_postions = [i.fit_i for i in current_swarm]
    #print [kernel_density_estimator(i, current_swarm_objective_postions) for i in pareto_front_positions]
    fitness = [(1/(kernel_density_estimator(i, current_swarm_objective_postions)+1)) for i in pareto_front_positions]
    total_fit = sum(fitness)
    roulette_wheel = len(fitness) * [fitness[0]/total_fit]
    for f in range(1,len(fitness)):
        roulette_wheel[f] = roulette_wheel[f-1] + fitness[f]/total_fit
    return roulette_wheel

#----------PARTICLE CLASS----------#

class Particle:
    def __init__(self, x0):
        self.position_i = [random.uniform(-10,10) for i in range(num_parameter_dimensions)]                                                                     #particle position
        self.velocity_i = [random.uniform(-5,5) for i in range(num_parameter_dimensions)]        #particle velocity
        self.pos_best_i = []                                                                     #particle's best position
        self.leader_i = []                                                                       #particle's leader
        self.fit_i = []                                                                          #particle fit 
        self.fit_best_i = []                                                                     #particle best fit

    #find particle's current fit
    def evaluate(self, costFunc, initial_evaluation=False):
        self.fit_i = costFunc(self.position_i) 
        
        # check is this is a personal best
        if initial_evaluation==False:
            if pareto_test(self.fit_i,self.fit_best_i) == True:
                self.pos_best_i = self.position_i
                self.fit_best_i = self.fit_i
                
        if initial_evaluation==True:
            self.fit_best_i = self.fit_i
            self.pos_best_i = self.position_i

            
    # update new velocity
    def update_velocity(self, pos_best_g):
        w = 0.5                      #inertia constant
        c1 = 2.0                    #cognitive parameter
        c2 = 1.0                    #social parameter
        
        for i in range(0, num_parameter_dimensions):
            r1 = random.random()
            r2 = random.random()
            velocity_cognitive = c1 * r1 * (self.pos_best_i[i] - self.position_i[i])
            velocity_social = c2 * r2 * (self.leader_i[i] - self.position_i[i])
            self.velocity_i[i] = w*self.velocity_i[i] + velocity_cognitive + velocity_social
    
    # update new position using new velocity
    def update_position(self, bounds):
        
        for i in range(0,num_parameter_dimensions):
            self.position_i[i]= self.position_i[i] + self.velocity_i[i]
            
            #adjust if particle goes above max bound
            if self.position_i[i] > bounds[i][1]:
                self.position_i[i] = bounds[i][1]
                self.velocity_i[i] = -1 * self.velocity_i[i]
                
            #adjust if particle goes below min bound
            if self.position_i[i] < bounds[i][0]:
                self.position_i[i] = bounds[i][0]
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


#-------------MOPSO CLASS--------------#

class MOPSO:
    
    def __init__(self, costFunc, bounds, num_particles, maxiter):
        global pareto_front
        global num_parameter_dimensions
        num_parameter_dimensions = len(bounds)
        
        #initialise the swarm
        swarm = []
        for i in range(0, num_particles):
            swarm.append(Particle(bounds))
            swarm[i].evaluate(costFunc, initial_evaluation=True)
        print 'FIRST SWARM', [j.fit_i for j in swarm]
        swarm_history.append([j.fit_i for j in swarm])
        proposed_pareto = [[j.position_i,j.fit_i] for j in swarm]
        print proposed_pareto
        find_pareto_front(proposed_pareto)
        pareto_history.append(pareto_front)
        print 'FIRST PARETO', [j[1] for j in pareto_front]
        
        #begin optimisation 
        i = 0
        
        while i < maxiter:
            #print 'iteration', i
            #print 'front', [j.fit_i for j in pareto_front]
            #calculate fit for swarm
            leader_roullete_wheel = get_leader_roulette_wheel(swarm)
            for j in range(0, num_particles):
                swarm[j].select_leader(leader_roullete_wheel)
                swarm[j].evaluate(costFunc)
            
            # update all velocities and positions   
            for j in range(0,num_particles):
                swarm[j].update_velocity(swarm[j].leader_i)
                swarm[j].update_position(bounds)
                
            proposed_pareto = [[j.pos_best_i,j.fit_best_i] for j in swarm] + pareto_front
            find_pareto_front(proposed_pareto)
            swarm_history.append([j.fit_i for j in swarm])
            pareto_history.append(pareto_front)
            print 'length of pareto = ',len(pareto_front)
            i += 1
        
        print 'FINAL PARETO', [j[1] for j in pareto_front]
        
        plt.ion()
        
        for i in range(len(pareto_history)):
            plt.cla()
            #plt.xlim([-1,50])
            #plt.ylim([-1,50])
            plt.xlim([-20,-5])
            plt.ylim([-10,5])
            plt.xlabel('f1(x)')
            plt.ylabel('f2(x)')
            plt.grid()
            x1 = [j[1][0] for j in pareto_history[i]]
            y1 = [j[1][1] for j in pareto_history[i]]
            x2 = [j[0] for j in swarm_history[i]]
            y2 = [j[1] for j in swarm_history[i]]
            plt.scatter(x1,y1,color='r')
            if i<len(pareto_history)-1:
                plt.scatter(x2,y2,color='black', alpha=0.4)
            plt.pause(0.5)
        while True:
            plt.pause(0.01)
#-------------RUN---------------#
bounds=[(-5,5),(-5,5),(-5,5)]
#bounds=[(-20,20)] # input bounds [(x1_min,x1_max),(x2_min,x2_max)...]
MOPSO(kursawe_test_objective_function,bounds,num_particles=20,maxiter=15)
