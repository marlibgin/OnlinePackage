from __future__ import division

import random
import math


def kur(x):
    "standard MOEA test problem KUR"
    N = 3
    f0 = 0
    for i in range(N-1):
        f0 = f0 + -10 * math.exp(-0.2 * math.sqrt(x[i] ** 2 + x[i+1] ** 2))
    f1 = 0
    for i in range(N):
        f1 = f1 + abs(x[i]) ** 0.8 + 5 * math.sin(x[i] ** 3)
    return (f0, f1)


def mkur(x):
    "standard MOEA test problem KUR"
    N = 8
    f0 = 0
    for i in range(N-1):
        f0 = f0 + -10 * math.exp(-0.2 * math.sqrt(x[i] ** 2 + x[i+1] ** 2))
    f1 = 0
    for i in range(N):
        f1 = f1 + abs(x[i]) ** 0.8 + 5 * math.sin(x[i] ** 3)
    return (f0, f1)

def matFunc(x):
    f = 0.26*(x[0]**2 + x[1]**2) - 0.48*x[0]*x[1]
    return f


# Can consider h, i and j to be a group
mach_mapping = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
mach_setting = [8, 6, 4, 3, 6, 8, 2, 5.1, 4.8, 5]

def lookup(pv):
    index = mach_mapping.index(pv)
    return mach_setting[index]

def weighted_sum(weights):
    result = 0

    for weight, value in zip(weights, mach_setting):
        result += weight * value

    return result

def power_sum(weights, powers):
    result = 0

    for weight, power, value in zip(weights, powers, mach_setting):
        result += weight * value ** power

    return result

def caget(pv):

    result = None

    if pv == 'r1':
        result = weighted_sum([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])

    elif pv == 'r2':
        result = weighted_sum([-1, -2, -2, -1, -1, -1, -1, -4, -4, -4])

    elif pv == 'r3':
        result = weighted_sum([0, 0, 0, 0, 0, 0, 0, 4, 4, 4])

    elif pv == 'r4':
        result = weighted_sum([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])

    elif pv == 'r5':
        result = power_sum([1]*10, [1, 0.2, 1.1, 2, 1.5, 2, 0.3, 1, 1, 1])

    elif pv == 'kur1':
        result = kur([lookup('a'), lookup('b'), lookup('c')])[0]

    elif pv == 'kur2':
        result = kur([lookup('a'), lookup('b'), lookup('c')])[1]

    elif pv == 'mkur1':
        result = kur([lookup('a'), lookup('b'), lookup('c'), lookup('d'), lookup('e'), lookup('f'), lookup('g'), lookup('h')])[0]

    elif pv == 'mkur2':
        result = kur([lookup('a'), lookup('b'), lookup('c'), lookup('d'), lookup('e'), lookup('f'), lookup('g'), lookup('h')])[1]

    elif pv == 'mat':
        result = matFunc([lookup('a'), lookup('b')])

    elif pv in mach_mapping:
        result = lookup(pv)
        return result

    result = random.normalvariate(result, result / 40)
    check_string = "Current model state:\n"
    for i, n in enumerate(mach_mapping):
        check_string += "                    {0} : {1}\n\n".format(n, mach_setting[i])
    #print check_string
    return result


def caput(pv, value):
    index = mach_mapping.index(pv)
    mach_setting[index] = value
