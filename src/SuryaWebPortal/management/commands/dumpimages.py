'''
Created on Nov 1, 2010

@author: surya
'''

import os
import sys
import json
import time

from datetime import datetime
from Collections.SuryaUploadData import *
from Collections.SuryaGroundTruth import *
from Collections.SuryaDeploymentData import *
from Collections.SuryaProcessingList import *
from Collections.SuryaCalibrationData import *
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = 'calibrationfile'
    help = 'Initializes the Server: \n 1. Checks if mongod is running \n 2. Checks if mongoengine is installed'
     
    def handle(self, *args, **options):
        ''' The SuryaWebPortal initialization method.
        '''
        
        # Check if we have the right number of arguments
        if len(args) != 1:
            raise CommandError('Error insufficient params: use ./manage.py init -help for info')
        
        # Check if mongod, is running
        isMongod = False
        processes = os.popen('''ps axo "%c"''')
        for process in processes:
            if 'mongod' in process:
                isMongod = True
        
        if not isMongod:
            raise CommandError('Error please run mongod first')
        
        # Import mongoengine and connect to the database
        try:
            import mongoengine
        except:
            raise CommandError('Error importing from mongoengine. Please ensure that mongoengine is installed')
        
        # Drop the database SuryaDB (This Implies That we lose all the stored images as well)
        mongoengine.connect('SuryaDB', tz_aware=True)

        startdate = datetime(2013,4,10,0,0,0)
        dirpre = "data/WI_data/"
        res = SuryaUploadData.objects(Q(deploymentId="madison.wi.bc") & Q(serverDatetime__gte = startdate))
        for up in res:
            fd = open(dirpre + json.loads(up.misc)['origfilename'], 'wb')
            fd.write(up.origFile.read())
            fd.flush()
            fd.close()
        
