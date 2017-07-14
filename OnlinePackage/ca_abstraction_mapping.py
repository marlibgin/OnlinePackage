from __future__ import division

import pkg_resources
from audioop import avg
#pkg_resources.require('cothread')

#from cothread.catools import caget, caput, ca_nothing
#from cothread.cadef import CAException
#import cothread


def lt_proxy():

    return caget("SR-DI-COUNT-01:MEAN")/caget("SR-DI-DCCT-01:SIGNAL")









name_to_function_mapping = {"lt-proxy" : lt_proxy}
