'''
Created on Nov 1, 2010

@author: surya
'''

import sys
import json
import logging
from mongoengine import *

from datetime import datetime
from Logging.Logger import getLog
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from Collections.SuryaUploadData import *
from Collections.SuryaDeploymentData import *
from Collections.SuryaProcessingList import *
from Collections.SuryaCalibrationData import *

from SuryaWebPortal.utils.postparser import *
from SuryaWebPortal.exceptions.UploadException import UploadException 

import mongoengine

# Connect to MongoDB
connect('SuryaDB', tz_aware=True)

log = getLog('views')
log.setLevel(logging.DEBUG)


# The cell phone expect the following line as an OK signal in the first line
CUSTOMIZED_PHONE_STATUS_OK   = "upok "
CUSTOMIZED_PHONE_STATUS_FAIL = "svrfail "





def get_post_config():
    # (required, type, db_name, default, parser)
    return { \
        "device_id": PostParserArgs(True, "string", "device_id", "None", None), \
        "aux_id": PostParserArgs(False, "string", "aux_id", "", None), \
        "misc": PostParserArgs(False, "string", "misc", "", None), \
        #"record_datetime": PostParserArgs(True, "datetime", "record_datetime", datetime.now(), lambda x: datetime.fromtimestamp(float(x)/1000.0)), \
        "record_datetime": PostParserArgs(True, "datetime", "record_datetime", datetime.now(), lambda x: eval ("datetime(" + x + ")")), \
        "gps_latitude": PostParserArgs(False, "float", "gps_latitude", 0.0, None), \
        "gps_longitude": PostParserArgs(False, "float", "gps_longitude", 0.0, None), \
        "gps_altitude": PostParserArgs(False, "float", "gps_altitude", 0.0, None), \
        "mimetype": PostParserArgs(True, "string", "mimetype", "type/none", None), \
        "deployment_id": PostParserArgs(True, "string", "deployment_id", "Deployment", None), \
        "version": PostParserArgs(True, "string", "version", "0.0", None), \
        "tag": PostParserArgs(False, "string", "tag", "", None), \
        "datatype": PostParserArgs(True, "string", "datatype", "none", None)
        }




@csrf_exempt
def upload_image(request):
    ''' This view gets invoked when uploading data to the server. The 
        post params are validated and stored in the SuryaUploadData
        Collection and the data files uploaded are stored in GridFS
    '''

    pp = PostParser(get_post_config())
    
    if (request.method == 'POST'):
        
        try:
            
            invalid_reason = ""
            
            server_datetime = datetime.now()

            post_crit_error = pp.parse(request.POST)            
            file_crit_error = False

            strMeta = ""
                       
            if 'data' not in request.FILES:
                file_crit_error = True
                invalid_reason += " -- MISSING DATA FILE"
                #raise UploadException("[ Sanity ] Missing mandatory field [data] in POST fields.")       

            if post_crit_error:
                invalid_reason = pp.get_log() + " -- Error parsing Post" + invalid_reason
                strMeta = invalid_reason + " Not Valid: " + str(post_crit_error or file_crit_error)
            else:
                strMeta = pp.get_log() + invalid_reason + " -- Not Valid: " + str(post_crit_error or file_crit_error)

            #Get Server Time String
            datetime_str = server_datetime.strftime("%Y%m%d.%H%M%S.") # e.g '20100702.174502.' 
            data_filename = datetime_str + pp.device_id + ".jpg"
            data_orig_filename = datetime_str + pp.device_id + "-orig.jpg"

            ######################################
            # Prepare saving meta info to database
            try:
                #Save metadata to DB   
                dbRecord = SuryaUploadData(
                deviceId = pp.device_id, \
                serverDatetime = server_datetime, 
                filename = data_filename,
                auxId = pp.aux_id, \
                misc = pp.misc, 
                recordDatetime = pp.record_datetime, \
                gpsLatLong = [pp.gps_latitude, pp.gps_longitude], \
                gpsAltitude = pp.gps_altitude, \
                datatype = pp.datatype, \
                mimetype = pp.mimetype, \
                tag = pp.tag, \
                version = pp.version, \
                validFlag = not (post_crit_error or file_crit_error), \
                invalidReason = invalid_reason, \
                deploymentId = pp.deployment_id)
                
                try:
                    # Save uploaded image into the work space. We may resize
                    dbRecord.file.new_file(filename = data_filename, content_type = 'image/jpeg')
                    for chunk in request.FILES['data'].chunks():
                        dbRecord.file.write(chunk)
                    dbRecord.file.close()

                    # Save original uploaded image
                    dbRecord.origFile.new_file(filename = data_orig_filename, content_type = 'image/jpeg')
                    for chunk in request.FILES['data'].chunks():
                        dbRecord.origFile.write(chunk)
                    dbRecord.origFile.close()
                    dbRecord.save()
                    
                except Exception, e:
                    try:
                        log.error("[ SavingFile ] Erroers while attempting to save the uploading file. " + str(e) + " <br/> Details: <br/>" + str(sys.exc_info()[1])) + " " + strMeta
                        dbRecord.validFlag = False
                        dbRecord.invalidReason = dbRecord.invalidReason + " -- Error trying save file and record: " + str(e)
                        dbRecord.save()
                    except:
                        raise UploadException("[ SavingFile ] Errors while attempting to save the uploading file. <br/> Details: <br/>" + str(sys.exc_info()[1]))

                
                if not post_crit_error and not file_crit_error:

                    bcStripData, calibData, pprocData = None, None, None
                        
                    # This method varies from application to application gotta make it generic
                    #Save this dbRecord reference in the ProcessList, get default processing data
                    # TODO invoke this as a method
                        
                    for item in SuryaDeploymentData.objects(deploymentId=pp.deployment_id):
                        # currently no datetime check, no validation as in if any one of the following is missing 
                        # this item doesn't get added to the process list
                        
                        if isinstance(item.calibrationId, SuryaImageAnalysisBCStripData):
                            log.info('got bcstrip data')
                            bcStripData = item.calibrationId
                        elif isinstance(item.calibrationId, SuryaImageAnalysisCalibrationData):
                            log.info('got img analysis calib data')
                            calibData = item.calibrationId
                        elif isinstance(item.calibrationId, SuryaImagePreProcessingCalibrationData):
                            log.info('got img pre proc calib data')
                            pprocData = item.calibrationId

                    if bcStripData is None or calibData is None or pprocData is None:
                        # no try block for now since this worked above
                        dbRecord.validFlag = False
                        dbRecord.invalidReason = dbRecord.invalidReason + " -- No calibration data for this deployment ID!"
                        dbRecord.save()
                    else:
                        SuryaIANAProcessingList(processEntity=dbRecord,
                                                processingFlag=False,
                                                processedFlag=False,
                                                overrideFlag=True, 
                                                preProcessingConfiguration=pprocData, 
                                                computationConfiguration=calibData, 
                                                bcStrips=bcStripData).save()
                 
            except Exception as e:
                raise UploadException("[ AccessDatabase ] Errors while attempting to save meta info to the suryaDB database." + \
                                      " <br/> Details: <br/>" + str(sys.exc_info()[1]) + " " + strMeta + " " + str(e))

        except UploadException as ue:
            log.error(ue.str)
            strRet = CUSTOMIZED_PHONE_STATUS_FAIL + ":" + ue.str
        except:
            log.critical("[ Developer ] Unhandling Exception: " + str(sys.exc_info()[1]))
            strRet = CUSTOMIZED_PHONE_STATUS_FAIL + ":" + str(sys.exc_info()[1])
        else:
            #################################
            # Prepare for returning & logging

            strRet = CUSTOMIZED_PHONE_STATUS_OK
            strRet += "Your uploading file has been stored at " + data_filename + ". \n"
            strRet += strMeta
            log.info("[ test_tag ] " + strRet)
        

        return HttpResponse(content=strRet, mimetype=None, status=200, content_type='text/html')
    
    else:
        log.error('[ Protocol ] Received a non POST request')
        return HttpResponse('Server accepts only HTTP POST messages')
