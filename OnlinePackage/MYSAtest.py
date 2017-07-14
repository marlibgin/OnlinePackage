import MYSA
import modelClass

interactor = modelClass.basicInteractor()
settings = {'initValues': [], 'anealPlot': 100, 'noIterations': 40, 'noAneals': 3000,'failDropCount': 400,'passOutTempDrop': [0.9,0.9], 'passInTempDrop': [0.8,0.8,0.8],'paramCount': 3, 'objCount': 2, 'objCallStop': 100000000}
maxs = [0.05,0.05,3]
mins = [0 for i in range(3)]
optimiser = MYSA.optimiser(settings, interactor, '/Users/greghenderson/downloads/onlinepackage-greg/onlinepackage/basic', mins, maxs)
optimiser.optimise()
print optimiser.domFrontObjectives
