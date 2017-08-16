from __future__ import division
import math

import pkg_resources
from audioop import avg
pkg_resources.require('cothread')

from cothread.catools import caget, caput, ca_nothing
from cothread.cadef import CAException
import cothread

bunch_number = 100

def define_bunch_number(new_bunch_number):
    global bunch_number
    bunch_number  = new_bunch_number


def bunch_length(I_beam):
    global bunch_number
    bunch_length = 11.85 + 9.55*((I_beam/bunch_number)**0.75)
    return bunch_length


def lifetime_proxy():
    
    PMT_count = caget('SR-DI-COUNT-01:MEAN')
    I_beam = caget('SR-DI-DCCT-01:SIGNAL')
    epsilon_y = caget('SR-DI-EMIT-01:VEMIT-MEAN')
    
    bunch_length = bunch_length(I_beam)
    
    objective = (PMT_count*I_beam)/(bunch_length*math.sqrt(epsilon_y))
    
    return objective
    

name_to_function_mapping = {"lifetime_proxy" : lifetime_proxy}




