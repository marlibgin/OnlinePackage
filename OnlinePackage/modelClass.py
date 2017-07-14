import model
class basicInteractor:

    #this is a very simple class for testing the basics of an algorithm

    def __init__(self):
        self.parameters = []

    def set_ap(self, x):
        self.parameters = x

    def get_ar(self):
        #first returns as a tuple
        ke = model.kur(self.parameters)
        f = [measurementTest('test',ke[i]) for i in range(2)]
        return f

class measurementTest:
    def __init__(self, name, mean):
        self.name = name
        self.mean = mean
        self.err = 0
