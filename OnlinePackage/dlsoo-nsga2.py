'''

Version 3
2016-08-01 15:00

'''
#!/bin/env dls-python
"fast non-dominated sorting genetic algorithm II"

import random, sys
import time
import os

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



store_address = None
completed_generation = None



# colour display codes
ansi_red = "\x1B[31m"
ansi_normal = "\x1B[0m"

# cache of solutions
memo = {}

class solution(tuple):
    pass


def crowded_comparison_key(x):
    # prefer low rank, then large distance (less crowded)
    print x
    return (x.rank, -x.distance)

def nothing_function(data):
    pass

def remove_prop_duplicates(initial_list):
    new_list = []
    new_list_see = []


    for i in initial_list:
        i_see = i.x

        if i_see not in new_list_see:
            new_list.append(i)
            new_list_see.append(i_see)

    return new_list


class optimiser:

    #def __init__(self, interactor, store_location, population_size, generations, param_count, result_count, min_var, max_var, pmut=None, pcross=0.9, eta_m=20, eta_c=20, individuals=None, seed=None, progress_handler=None):
    def __init__(self, settings_dict, interactor, store_location, a_min_var, a_max_var, individuals=None, progress_handler=None):

        self.memo = {}

        self.interactor = interactor
        self.store_location = store_location
        self.population_size = settings_dict['pop_size']
        self.generations = settings_dict['max_gen']
        self.param_count = settings_dict['param_count']
        self.result_count = settings_dict['result_count']
        self.min_var = a_min_var
        self.max_var = a_max_var
        self.pcross = settings_dict['pcross']
        self.eta_m = settings_dict['eta_m']
        self.eta_c = settings_dict['eta_c']

        if progress_handler == None:
            progress_handler = nothing_function

        self.progress_handler = progress_handler


        if settings_dict['pmut'] == None:
            settings_dict['pmut'] = 0.1 / param_count

        self.pmut = settings_dict['pmut']

        if individuals == None:
            temp = []
            for i in range(settings_dict['param_count']):
                temp.append((self.max_var[i] + self.min_var[i])/2)

            self.individuals = (temp,)
        else:
            self.individuals = individuals

        if settings_dict['seed'] == None:
            seed = time.time()

        self.seed = settings_dict['seed']
        self.add_current_to_individuals = settings_dict['add_current_to_individuals']

        self.pause = False

        #print "self.individuals: {0}".format(self.individuals)
        #print "self."
        print "interactor.param_var_groups: {0}".format(interactor.param_var_groups)
        print "interactor.measurement_vars: {0}".format(interactor.measurement_vars)

    def save_details_file(self):

        file_return = ""

        file_return += "NSGA-II algorithm\n"
        file_return += "=================\n\n"
        file_return += "Generations: {0}\n".format(self.generations)
        file_return += "Population size: {0}\n\n".format(self.population_size)

        file_return += "Parameter count: {0}\n".format(self.param_count)
        file_return += "Results count: {0}\n\n".format(self.result_count)

        file_return += "Minimum bounds: {0}\n".format(self.min_var)
        file_return += "Maximum bounds: {0}\n\n".format(self.max_var)

        file_return += "p_mut: {0}\n".format(self.pmut)
        file_return += "p_cross: {0}\n".format(self.pcross)
        file_return += "eta_m: {0}\n".format(self.eta_m)
        file_return += "eta_c: {0}\n\n".format(self.eta_c)

        file_return += "Seed: {0}\n".format(self.seed)
        file_return += "Individuals: {0}".format(self.individuals)

        return file_return


    def make_solution(self, x, y):
        p = solution([i.mean for i in y])
        p.x = x
        p.unc = [i.err for i in y]
        return p

    def dom(self, a, b):
        "a weakly dominates b"
        # An individule which is the same in all respects
        # does not dominate the other individule
        if all([a0 == b0 for (a0, b0) in zip(a, b)]):
            return False
        # but if any respect is better then the other
        # individule is dominated
        d = True
        for (a0, b0) in zip(a, b):
            d = (a0 <= b0) and d
        return d

    def test_front(self, fs):
        "check that no member of the non-dominated front dominates another"
        for p0 in fs:
            for p1 in fs:
                if self.dom(p0, p1):
                    print "front violation!", p0, p1
                    sys.exit(1)

    def find_nondominated_front(self, P):
        # front is empty
        front = []
        for p0 in P:
            # add p0 to front temporarily
            front.append(p0)
            for p1 in P:
                if self.dom(p1, p0):
                    # it's dominated, take it off the front
                    front.pop()
                    # p0 has been rejected, no need to keep looking
                    break
        # check here
        # test_front(front)
        return front

    def fast_non_dominated_sort(self, P):
        Fs = []
        P = set(P)
        i = 0
        while len(P) > 0:
            F = self.find_nondominated_front(list(P))
            P = P - set(F)
            # assign non-dominated rank
            for f in F:
                f.rank = i
            Fs.append(F)
            i += 1
        return Fs

    def crowding_distance_assignment(self, front):
        l = len(front)
        for f in front:
            f.distance = 0
        # sort by each objective in turn
        for m in range(len(front[0])):
            s = sorted(front, key = lambda x: x[m])
            s[0].distance = float('inf')
            s[-1].distance = float('inf')
            for i in range(1, l-1):
                s[i].distance = s[i].distance + s[i + 1][m] - s[i - 1][m]
    '''
    def crowded_comparison_key(self, x):
        # prefer low rank, then large distance (less crowded)
        return (x.rank, -x.distance)
    '''
    def binary_tournament_selection(self, pop):
        # already sorted by fitness
        idx = range(len(pop))
        p1 = random.choice(idx)
        p2 = random.choice(idx)
        return pop[min(p1, p2)]

    def selection(self, pop):
        return [self.binary_tournament_selection(pop) for n in range(len(pop))]

    def polynomial_mutation(self, p):
        pmut_real = self.pmut
        eta_m = self.eta_m
        min_realvar = self.min_var
        max_realvar = self.max_var
        N = len(p)
        q = p[:]
        for n in range(N):
            if random.random() > pmut_real:
                continue
            y = p[n]
            yl = min_realvar[n]
            yu = max_realvar[n]
            delta1 = (y-yl)/(yu-yl)
            delta2 = (yu-y)/(yu-yl)
            rnd = random.random()
            mut_pow = 1.0/(eta_m+1.0)
            if rnd <= 0.5:
                xy = 1.0-delta1
                val = 2.0*rnd+(1.0-2.0*rnd)*(pow(xy,(eta_m+1.0)))
                deltaq = pow(val,mut_pow) - 1.0
            else:
                xy = 1.0-delta2
                val = 2.0*(1.0-rnd)+2.0*(rnd-0.5)*(pow(xy,(eta_m+1.0)))
                deltaq = 1.0 - (pow(val,mut_pow))
            y = y + deltaq*(yu-yl)
            if y<yl:
                y = yl
            if y>yu:
                y = yu
            q[n] = y
        return q

    def crossover(self, pop):
        Q = []
        for n in range(len(pop)/2):
            #print n
            (c1, c2) = self.sbx20(pop[n], pop[n+1])
            Q.append(c1)
            Q.append(c2)
        return Q

    def sbx20(self, p1, p2):
        pcross_real = self.pcross
        eta_c = self.eta_c
        min_realvar = self.min_var
        max_realvar = self.max_var
        # copy parents
        child1 = p1[:]
        child2 = p2[:]
        # crossover?
        if random.random() > pcross_real:
            return (child1, child2)
        # floating point epsilon
        EPS = 2 ** -52
        # number of variables
        N = len(child1)
        #print "N:{0}".format(N)
        #print "child1: {0}".format(child1)
        for n in range(N):
            # 50% chance of crossing this variable
            if random.random() > 0.5:
                continue
            # identical to machine precision, no crossover
            if abs(p1[n] - p2[n]) < EPS:
                continue
            y1 = min(p1[n], p2[n])
            y2 = max(p1[n], p2[n])
            yl = min_realvar[n]
            yu = max_realvar[n]
            rand = random.random()
            beta = 1.0 + (2.0*(y1-yl)/(y2-y1))
            alpha = 2.0 - pow(beta,-(eta_c+1.0))
            if rand <= 1.0/alpha:
                betaq = pow ((rand*alpha),(1.0/(eta_c+1.0)))
            else:
                betaq = pow ((1.0/(2.0 - rand*alpha)),(1.0/(eta_c+1.0)))
            c1 = 0.5*((y1+y2)-betaq*(y2-y1))
            beta = 1.0 + (2.0*(yu-y2)/(y2-y1))
            alpha = 2.0 - pow(beta,-(eta_c+1.0))
            if rand <= 1.0/alpha:
                betaq = pow ((rand*alpha),(1.0/(eta_c+1.0)))
            else:
                betaq = pow ((1.0/(2.0 - rand*alpha)),(1.0/(eta_c+1.0)))
            c2 = 0.5*((y1+y2)+betaq*(y2-y1))
            # bounds
            if c1<yl:
                c1=yl
            if c2<yl:
                c2=yl
            if c1>yu:
                c1=yu
            if c2>yu:
                c2=yu
            if random.random() > 0.5:
                child1[n] = c2
                child2[n] = c1
            else:
                child1[n] = c1
                child2[n] = c2
        return (child1, child2)

    def mutation(self, pop):
        return [self.polynomial_mutation(p) for p in pop]

    def memo_lookup(self, pop):
        done = []
        todo = []
        for p in pop:
            p = tuple(p)
            if p in self.memo:
                done.append((self.make_solution(p, self.memo[p])))
            else:
                todo.append(p)
        return (done, todo)

    def evaluate(self, pop):

        "evaluate population"
        #print "POP: {0}".format(pop)
        # now add memoization
        result = []

        # get any cached results
        # (randomly some members don't get mutated or crossed over)
        (already_done, todo) = self.memo_lookup(pop)

        # calculate new points
        ys = self.evaluate_link(pop)
        #print "ys: {0}".format(ys)

        # store results in cache
        for (x, y) in zip(todo, ys):
            self.memo[x] = y
            result.append(self.make_solution(x, y))

        result = result + already_done
        #print result
        return result

    def evaluate_link(self, population):
        data = []

        for in_pop in range(len(population)):
            # Configure machine for the measurement
            self.interactor.set_ap(population[in_pop])

            #data.append(self.interactor.get_ar())

            all_data = self.interactor.get_ar()
            #print "all_data: {0}".format(all_data)
            #print "population[in_pop]: {0}".format(population[in_pop])
            #print "hi mom!"
            #print ["get_ar() stds: {0}".format(i.dev) for i in all_data]
            #all_data = [i.mean for i in all_data] # Pull out just the means from the returned data
            data.append(all_data)

        #return [i[0] for i in data]
        return data

    def make_new_pop(self, pop):

        # only need inputs at this stage
        # (we are already sorted by fitness)
        pop = [list(p.x) for p in pop]

        pop = self.selection(pop)
        pop = self.crossover(pop)
        pop = self.mutation(pop)

        # now evaluate the new populuation members
        pop = self.evaluate(pop)

        return pop

    def random_population(self):
        "produce a random population within bounds"
        S = self.population_size
        min_realvar = self.min_var
        max_realvar = self.max_var
        N = len(min_realvar)
        X0 = []
        for s in range(S):
            x = [0] * N
            for n in range(N):
                lb = min_realvar[n]
                ub = max_realvar[n]
                x[n] = lb + (random.random()) * (ub - lb)
            X0.append(x)
        return X0

    def set_population_from_individules(self, pop):
        individules = self.individuals
        for i, individule in enumerate(individules):
            pop[i] = individule
        return pop
    '''
    def load_input(self, filename):
        options = {}
        # load variables in file into options structure
        execfile(filename, options)
        # some checks (better find out about missing parameters now than later)
        schema = (("pmut_real", "float"),
                  ("pcross_real", "float"),
                  ("eta_m", "float"),
                  ("eta_c", "float"),
                  ("evaluate", "function"),
                  ("min_realvar", "array"),
                  ("max_realvar", "array"),
                  ("population_size", "int"),
                  ("generations", "int"),
                  ("individules", "array"),
                  ("seed", "int"),
                  )

        fail = False
        print "NSGA-II"
        print "======="
        for (name, check) in schema:
            if not name in options:
                print "%sERROR: input '%s' is missing%s" % (ansi_red, name, ansi_normal)
                fail = True
            else:
                print "%s: %s" % (name, options[name])

        l1 = len(options["min_realvar"])
        l2 = len(options["max_realvar"])

        if l1 != l2:
            print "%sERROR: min_realvar is not the same length as max_realvar\n" \
                  "(should be number of INPUT variables)%s" % (ansi_red, ansi_normal)
            fail = True

        for (ml, mu) in zip(options["min_realvar"], options["max_realvar"]):
            if ml > mu:
                print "%sERROR: Maximum value must be greater than minimum value, but " \
                      "specified value is (%f < %f)%s" % (ansi_red, ml, mu, ansi_normal)

        for i in options["individules"]:
            if len(i) != l1:
                print "%sERROR: an individule must have the same length as" \
                      " the number of paramters%s" % (ansi_red, ansi_normal)
                fail = True
            for (ml, mu, ii) in zip(options["min_realvar"], options["max_realvar"], i):
                if not ml <= ii <= mu:
                    print "%sERROR: Individual out of range with paramter value %f%s" \
                            % (ansi_red, ii, ansi_normal)
                    fail=True

        if len(options["individules"]) > options["population_size"]:
            print "%sERROR: more individules specified than population %s" % (ansi_red, ansi_normal)
            fail = True

        if fail:
            sys.exit(1)

        return options
    '''
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

    def optimise(self):

        global store_address
        global completed_generation
        store_address = self.store_location

        "Non-dominated sorting genetic algorithm II main loop"
        '''
        if not sys.argv[1:]:
            print 'Usage: ' + sys.argv[0] + ' <nsga_input_file.py>'
            print
            print 'Non-dominated Sorting Genetic Algorithm II'
            sys.exit(1)

        # load problem
        global options
        options = load_input(sys.argv[1])
        '''
        # Make the save directory
        if not os.path.exists(self.store_location):
            os.makedirs(self.store_location)

        if self.add_current_to_individuals:
            current_ap = self.interactor.get_ap()
            self.individuals = list(self.individuals)
            self.individuals[0] = current_ap

        # seed the random number generator to ensure repeatble results
        random.seed(self.seed)

        # initialize population
        X0 = self.random_population()
        X0 = self.set_population_from_individules(X0)
        P = self.evaluate(X0)
        Q = []
        print "X0: {0}".format(X0)
        print "P: {0}".format(P)

        # for each generation
        for t in range(self.generations):

            # combine parent and child populations
            R = P + Q


            # remove duplicates
            #R = list(set(R))
            R = remove_prop_duplicates(R)

            # find all non-dominated fronts
            fronts = self.fast_non_dominated_sort(R)

            # calculate the density of solutions around each point
            for f in fronts:
                self.crowding_distance_assignment(f)

            # sort first by rank (which front) then by sparsity
            R.sort(key = crowded_comparison_key)

            # take the best solutions that fit in our population size
            P = R[:self.population_size]

            # tournament, crossover, mutation
            Q = self.make_new_pop(P)

            # print out all solutions by front
            self.dump_fronts(fronts, t)

            # Signal progress
            print "generation %d" % t
            completed_generation = t
            self.progress_handler(float(t) / float(self.generations), t)
            while self.pause:
                self.progress_handler(float(t) / float(self.generations), t)

        print "DONE"
        #self.progress_handler(t+1)


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
