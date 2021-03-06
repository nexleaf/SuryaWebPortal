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
        #SuryaUploadData.drop_collection()
        #SuryaGroundTruth.drop_collection()
        #SuryaDeploymentData.drop_collection()
        #SuryaCalibrationData.drop_collection()
        #SuryaProcessingList.drop_collection()
        
        # Initialize the DB with default Calibration data.            
        calibrationDataList = json.loads(open(args[0],'r').read())
        
        for calibrationDataEntry in calibrationDataList:
            calibid = int(calibrationDataEntry.get("calibrationId"))
            cbdo = SuryaCalibrationData.objects(calibrationId=calibid)
            if len(cbdo) == 0:
                type = calibrationDataEntry.get("type")
                self.stdout.write("Working on %s %s\n" % (type, calibrationDataEntry.get("calibrationId")))
                self.stdout.write("Debug: \n\n%s\n\n" % (str(calibrationDataEntry)))
                self.stdout.write("BCDetector: %s" % (str(calibrationDataEntry.get("bcDetectorType"))))
                if  type == "compu":
                    calibrationData = SuryaImageAnalysisCalibrationData(calibrationId = calibrationDataEntry.get("calibrationId"),
                                                                        exposedTime   = calibrationDataEntry.get("exposedTime"),
                                                                        timeUnits     = calibrationDataEntry.get("timeUnits"),
                                                                        airFlowRate   = calibrationDataEntry.get("airFlowRate"),
                                                                        filterRadius  = calibrationDataEntry.get("filterRadius"),
                                                                        bcArea        = calibrationDataEntry.get("bcArea"),
                                                                        bcDetectorType = calibrationDataEntry.get("bcDetectorType"))
                    self.stdout.write("Saving compu %d - %s\n" % (calibrationData.calibrationId, calibrationData.bcDetectorType))
                    calibrationData.save()
                if type == "pproc":
                    calibrationData = SuryaImagePreProcessingCalibrationData(calibrationId = calibrationDataEntry.get("calibrationId"),
                                                                       dp = calibrationDataEntry.get("dp"),
                                                                       minimumRadius = calibrationDataEntry.get("minimumRadius"),
                                                                       maximumRadius = calibrationDataEntry.get("maximumRadius"),
                                                                       highThreshold = calibrationDataEntry.get("highThreshold"),
                                                                       accumulatorThreshold = calibrationDataEntry.get("accumulatorThreshold"),
                                                                       samplingFactor = calibrationDataEntry.get("samplingFactor"),
                                                                       samplingFactorFixed = calibrationDataEntry.get("samplingFactorFixed"),
                                                                       minimumDistance = calibrationDataEntry.get("minimumDistance"))
                    self.stdout.write("Saving pproc %d\n" % calibrationData.calibrationId)
                    calibrationData.save()
                if type == "bcstrip":
                    calibrationData = SuryaImageAnalysisBCStripData(calibrationId = calibrationDataEntry.get("calibrationId"),
                                                                bcStrips = calibrationDataEntry.get("bcStrips"))
                    self.stdout.write("Saving bcstrip %d\n" % calibrationData.calibrationId)
                    calibrationData.save()
            
            deploymentDataList = calibrationDataEntry.get("deploymentIds")
            # Initialize the DB with default DeploymentId to CalibrationData mapping
            for deploymentDataEntry in deploymentDataList:
                deplstr = deploymentDataEntry.get("deploymentId")
                calibobj = SuryaCalibrationData.objects.get(calibrationId=calibid)
                (sdd, created) = SuryaDeploymentData.objects.get_or_create(deploymentId=deplstr, activateDatetime=datetime(*deploymentDataEntry.get("activateDatetime")), calibrationId=calibobj)
                if created:
                    self.stdout.write("Creating depl: %s with id %d\n" % (deplstr, calibid))
                    sdd.activateDatetime=datetime(*deploymentDataEntry.get("activateDatetime"))
                else:
                    self.stdout.write("Verified: %s with id %d\n" % (deplstr, calibid))
                sdd.save()
                # 
                #SuryaDeploymentData(deploymentId=deploymentDataEntry.get("deploymentId"),
                #                    activateDatetime=datetime(*deploymentDataEntry.get("activateDatetime")),
                #                    calibrationId=calibrationData).save()
                
        # Run the Django Webserver
        #os.popen('''/home/surya/ProjectSurya/SuryaWebPortal/src/SuryaWebPortal/manage.py runserver &''')
        
        # Initialize the Image Analysis Controller.
        #os.popen('''python /home/surya/ProjectSurya/SuryaIANAFramework/src/IANA/IANAFramework.py &''')
        
        # Start the gmail monitor.
        #os.popen('''python /home/surya/ProjectSurya/SuryaIANAGmailPortal/src/GmailMonitor/IANAGmailMonitor.py &''')
        
        # Result Mailer.
        #os.popen('''python /home/surya/ProjectSurya/SuryaIANAGmailPortal/src/GmailResults/IANAGmailResults.py &''')
