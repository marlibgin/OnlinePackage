from __future__ import division

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





mach_state = [0, 0, 0]

def caput(pv, value):
    if pv == "a":
        mach_state[0] = value
    elif pv == "b":
        mach_state[1] = value
    elif pv == "c":
        mach_state[2] = value

def caget(pv):
    my_return = 0
    
    if pv == "d":
        my_return = kur(mach_state)[0]
    elif (pv == "e"):
        my_return = kur(mach_state)[1]
    
    return my_return