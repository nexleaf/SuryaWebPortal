
import sys
import json
import logging
from mongoengine import *

from datetime import datetime
from Logging.Logger import getLog
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from SuryaWebPortal.models import MyUser
from Validation import Validate

from Collections.SuryaUploadData import *
from Collections.SuryaGroundTruth import *
from Collections.SuryaDeploymentData import *
from Collections.SuryaProcessingList import *
from Collections.SuryaProcessResult import *
from Collections.SuryaCalibrationData import *


import mongoengine

# Connect to MongoDB
connect('SuryaDB', tz_aware=True)

log = getLog('views')
log.setLevel(logging.DEBUG)


@login_required
def deployments(request):
    if request.user.is_superuser:
        deployments = SuryaUploadData.objects.distinct('deploymentId')
    else:
        user_deployments = MyUser.objects.get(id=request.user.id).deployment_list()
        deployments = []
        for d in SuryaUploadData.objects.distinct('deploymentId'):
            if d in user_deployments:
                deployments.append(d)
    deployments.sort()
    t = loader.get_template('debug/deployments.html')
    c = RequestContext(request, {'deployments':deployments})
    return HttpResponse(t.render(c))

@login_required
def view_deployment(request, deploymentId):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))
    
    uploads = SuryaUploadData.objects(deploymentId=deploymentId).order_by('-serverDatetime')
    return render_to_response('debug/view_deployment.html', {
            'uploads':uploads,
            'dep_id':deploymentId,
            }, context_instance=RequestContext(request))
    #}, context_instance=RequestContext(request))
    #t = loader.get_template('debug/view_deployment.html')
    #c = RequestContext(request, {'uploads':uploads, 'dep_id':deploymentId})
    #return HttpResponse(t.render(c))

@login_required
def view_upload(request, deploymentId, objId):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))
    
    upload = SuryaUploadData.objects.with_id(objId)
    flowratestr = "cc/m"
    try:
        result = SuryaIANAResult.objects.get(item=upload)
        if result.computationConfiguration.airFlowRate < 20:
            flowratestr = "l/m"
        warn, warnmsg = Validate.validate(result)
    except SuryaIANAResult.DoesNotExist:
        try:
            result = SuryaIANAFailedResult.objects.get(item=upload)
        except SuryaIANAFailedResult.DoesNotExist:
            result = None
    t = loader.get_template('debug/view_upload.html')
    c = RequestContext(request, {'up':upload, 'dep_id':deploymentId, 'result':result, 'item':result, 'flowratestr':flowratestr, 'warn': warn, 'warnmsg': warnmsg})
    return HttpResponse(t.render(c))

@login_required
def debug(request):
    if not request.user.is_staff:
        return redirect('SuryaWebPortal.views.home.home')
    
    t = loader.get_template('debug/debug.html')
    c = RequestContext(request, {})
    return HttpResponse(t.render(c))

@login_required
def uploads(request, objID=None):
    if not request.user.is_staff:
        return redirect('SuryaWebPortal.views.home.home')
    
    t = loader.get_template('debug/uploads.html')
    if objID is None:
        c = RequestContext(request, {'uploads' : SuryaUploadData.objects})
    else:
        c = RequestContext(request, {'uploads' : [SuryaUploadData.objects.with_id(objID)]})
    
    return HttpResponse(t.render(c))

@login_required
def results(request):
    if not request.user.is_staff:
        return redirect('SuryaWebPortal.views.home.home')
    t = loader.get_template('debug/results.html')
    c = RequestContext(request, {'results' : SuryaIANAResult.objects})
    return HttpResponse(t.render(c))


@login_required
def failures(request):
    if not request.user.is_staff:
        return redirect('SuryaWebPortal.views.home.home')
    if not request.user.is_staff:
        return redirect('SuryaWebPortal.views.home.home')
    t = loader.get_template('debug/failures.html')
    c = RequestContext(request, {'failures' : SuryaIANAFailedResult.objects})
    return HttpResponse(t.render(c))


