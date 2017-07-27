import pkg_resources
pkg_resources.require('cothread')
pkg_resources.require('matplotlib')
pkg_resources.require('numpy')
pkg_resources.require('scipy')
import datetime

import matplotlib.pyplot as plt
import cothread
from cothread.catools import caget

plt.ion()


dt = 0.1
t = []
obj = []


for i in range(200):
    plt.cla()
    PV_measurement = caget('BR01C-DI-PIN-17:RATE')  
    current_time = datetime.datetime.now()
    t.append(current_time)
    obj.append(PV_measurement)
    
    plt.plot_date(t,obj,marker='None',linestyle='-')
    plt.pause(0.1)

while True:
    plt.pause(0.01)
    