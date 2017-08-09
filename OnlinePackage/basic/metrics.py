'''
Performace metrics
This is a library that contains the metrics used to mesaure the performance for each algorithm.
@authors: Greg Henderson
'''

def distanceSquared(x1, x2):
    return sum([(x1[i] - x2[i])**2 for i in range(len(x1))])

def metric1(acturalFront, calculatedFront):
    average = 0
    for i in calculatedFront:
        minDist = min([distanceSquared(i, point) for point in acturalFront])**0.5
        average += minDist
    average = average/len(calculatedFront)
    return average

def metric2(calculatedFront, sigma):
    spread = 0
    for i in calculatedFront:
        spread += len([j for j in calculatedFront if distanceSquared(i, j) > sigma**2])
    if len(calculatedFront) == 1:
        return 1
    else:
        return float(spread)/float(len(calculatedFront) - 1)

def metric3(calculatedFront):
    spread = 0
    for i in range(len(calculatedFront[0])):
        distSet = []
        for j in range(len(calculatedFront)):
            for k in range(j+1, len(calculatedFront)):
                distSet += [abs(calculatedFront[j][i] - calculatedFront[k][i])]
        try:
            spread += max(distSet)
        except:
            pass
    return spread**0.5
