'''
Fast testing classes
This library contains the classes that can be used to test any algorithm without the GUI and runs fast. Note this uses the kursawe test.
@authors: Greg Henderson
'''
import kur_model
import dlsoo_mosa
import matplotlib.pyplot as plot
class measure:
    '''
    This is used as a basic measure class simular to the class used in the optimiser_util but simpler.
    '''
    def __init__(self, f):
        self.mean = f
        self.err = 0


class interactorFast:
    '''
    Simple interactor for kursawe made to be compatible with current get and set methods of interactors defined in dls_optimiser_util
    '''
    def __init__(self):
        self.params = [1,1,1]
        self.param_var_groups = [1,1,1]
        self.measurement_vars = [1,1]

    def set_ap(self, x):
        self.params = x

    def get_ar(self):
        f = kur_model.kur(self.params)
        result = []
        for i in f:
            result.append(measure(i))
        return result
