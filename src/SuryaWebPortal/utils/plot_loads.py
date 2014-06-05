


import sys
import json
import logging

from mongoengine import *

from datetime import datetime, timedelta
from Logging.Logger import getLog

from django.http import HttpResponse, HttpResponseNotFound
from django.template import Context, loader, RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import struct
import matplotlib.cm as cm
import numpy
import matplotlib.dates as mdates






def plot_loads_devs(response, start, alldata, allmeans, meandates, maxload, notesets):
    fig = Figure(figsize=(12,8), dpi=72)
    rect = fig.patch
    rect.set_facecolor('white')
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    colorlist = ['b', 'g', 'r', 'y', 'c']
    plts = []
    labels = []
    colorlist_count = 0
    for dev in alldata.keys():
        labels.append(dev)
        plt = ax.plot(alldata[dev]['dates'], alldata[dev]['loads'], colorlist[colorlist_count] + 'x')[0]
        plts.append(plt)
        colorlist_count += 1
    ax.plot(meandates, allmeans, 'ks')
    for i in range(len(meandates)):
        outstr = "%.03f ug/cm^2\n" % (allmeans[i])
        for j in notesets[i]:
            outstr += j + "\n"
        ax.text(meandates[i], allmeans[i], outstr)
    ax.set_ylabel('$ug/cm^2$')
    ax.set_xlabel('Image Record Time (from EXIF)')
    ax.set_title("%s" % (str(start)))
    fig.autofmt_xdate()
    ax.legend(plts, labels, numpoints=1, loc='lower right')
    fig.subplots_adjust(left=0.07, bottom=0.10, right=0.91, \
                        top=0.95, wspace=0.20, hspace=0.00)
    canvas.print_png(response)



def plot_grads(response, start, thedate, thedata, sampled):
    fig = Figure(figsize=(12,8), dpi=72)
    rect = fig.patch
    rect.set_facecolor('white')
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    pout = ax.plot(thedate, sampled, 'ok')
    pout = ax.plot(
        thedate, thedata[0], 'bx',
        thedate, thedata[1], 'gx',
        thedate, thedata[2], 'rx',
        thedate, thedata[3], 'cx',
        thedate, thedata[4], 'mx',
        thedate, thedata[5], 'yx',
        thedate, thedata[6], 'kx',
        thedate, thedata[7], 'bx',
        thedate, thedata[8], 'gx',
        thedate, thedata[9], 'rx',
        thedate, thedata[10], 'cx',
        thedate, thedata[11], 'mx'
        )
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M')
    ax.set_ylim(0,300)
    ax.set_title(start.strftime("%Y-%m-%d %H:%M:%S"))
    canvas.print_png(response)

