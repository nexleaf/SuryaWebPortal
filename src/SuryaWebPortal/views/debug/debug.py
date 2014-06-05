
import re
import sys
import json
import pytz
import logging
from mongoengine import *

from datetime import datetime
from datetime import timedelta
from Logging.Logger import getLog
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from SuryaWebPortal.models import MyUser
from SuryaWebPortal.forms.DataDownload import *
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


def just_date(inputdate):
    return datetime(inputdate.year, inputdate.month, inputdate.year, tzinfo=inputdate.tzinfo)

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
    
    uploads_all = SuryaUploadData.objects(deploymentId=deploymentId).order_by('-serverDatetime')
    pageup = Paginator(uploads_all, 50)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    
    try:
        uploads = pageup.page(page)
    except (EmptyPage, InvalidPage):
        uploads = pageup.page(pageup.num_pages)
    
    return render_to_response('debug/view_deployment.html', {
            'uploads':uploads,
            'dep_id':deploymentId,
            'form': DownloadDataForm()
            }, context_instance=RequestContext(request))
    #}, context_instance=RequestContext(request))
    #t = loader.get_template('debug/view_deployment.html')
    #c = RequestContext(request, {'uploads':uploads, 'dep_id':deploymentId})
    #return HttpResponse(t.render(c))

@login_required
def view_deployment_day(request, deploymentId, year, month, day):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))

    byrecord = True
    if request.GET.has_key('byrecord'):
        if request.GET.get('byrecord') == "False":
            byrecord = False

    page = datetime(year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC)
    page_end = page + timedelta(days=1)
    if byrecord:
        uploads = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(recordDatetime__gte = page) & Q(recordDatetime__lte = page_end)).order_by('-recordDatetime')
    else:
        uploads = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(serverDatetime__gte = page) & Q(serverDatetime__lte = page_end)).order_by('-serverDatetime')
        
    prevday = page - timedelta(days=1)
    
    return render_to_response('debug/view_deployment_day.html', {
        'uploads':uploads,
        'dep_id':deploymentId,
        'prevday':prevday,
        'nextday':page_end,
        'form': DownloadDataForm(),
        'year': year,
        'month': month,
        'day': day,
        'byrecord': byrecord
        }, context_instance=RequestContext(request))
    #}, context_instance=RequestContext(request))
    #t = loader.get_template('debug/view_deployment.html')
    #c = RequestContext(request, {'uploads':uploads, 'dep_id':deploymentId})
    #return HttpResponse(t.render(c))


@login_required
def view_deployment_grid(request, deploymentId):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))

    byrecord = True
    if request.GET.has_key('byrecord'):
        if request.GET.get('byrecord') == "False":
            byrecord = False    

    oneday = timedelta(days=1)
    
    try:
        page = datetime.strptime(request.GET.get('date', (datetime.now(pytz.UTC) + timedelta(days=2)).strftime("%Y%m%d")), "%Y%m%d")
    except ValueError:
        tempd = datetime.now(pytz.UTC) + timedelta(days=2)
        page = datetime(tempd.year, tempd.month, tempd.day, tzinfo=pytz.UTC)

    page_end = page - timedelta(days=91)
    page_next = page + timedelta(days=91)
    display_days = 9
    
    datestrs = []
    datecounts = []
    while page > page_end and display_days > 0:
        if byrecord:
            cnt = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(recordDatetime__gte = page) & Q(recordDatetime__lte = page + oneday)).count()
            if cnt > 0:
                datecounts.append((cnt,page))
                datestrs.append(page.strftime("%Y/%m/%d"))
                display_days = display_days - 1
        else:
            cnt = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(serverDatetime__gte = page) & Q(serverDatetime__lte = page + oneday)).count()
            if cnt > 0:
                datecounts.append((cnt,page))
                datestrs.append(page.strftime("%Y/%m/%d"))
                display_days = display_days - 1
        page = page - oneday
    
    return render_to_response('debug/view_deployment_grid.html', {
            'datecounts':datecounts[::-1],
            'datestrs':datestrs[::-1],
            'dep_id':deploymentId,
            'form': DownloadDataForm(),
            'prevday': page_end.strftime("%Y%m%d"),
            'nextday': page_next.strftime("%Y%m%d"),
            'byrecord': byrecord,
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
    warn = None
    warnmsg = ""
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


def validresult(upload):
    res = SuryaIANAResult.objects(item=upload)
    if res == None or len(res) == 0:
        return ''
    warn, warnmsg = Validate.validate(res[0])
    if warn == True:
        return ''
    elif warn == False:
        return 'Yes'
    else:
        return 'Unknwn'

def yesno(val):
    if val:
        return "Yes"
    else:
        return "No"


@login_required
def data_download_recordsort(request, deploymentId):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))
    start = None
    stop = None
    
    response = HttpResponse(mimetype='text/csv')
    if request.method == 'POST':
        form = DownloadDataForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data['startDateTime']
            stop = form.cleaned_data['stopDateTime']
        else:
            start = datetime.strptime(request.POST['startDateTime'], '%m/%d/%Y')
            stop = datetime.strptime(request.POST['stopDateTime'], '%m/%d/%Y')
            log.debug("Form is invalid")

    log.debug("Got dates %s %s" % (str(start), str(stop)))
    if start == None or stop == None:
        return response
        
    uploads = SuryaUploadData.objects(Q(deploymentId = deploymentId) & Q(serverDatetime__gte = start) & Q(serverDatetime__lte = stop)).order_by('+recordDatetime')

    saved_data = [];
    allcolumns = [];
    prevdate = datetime.now(pytz.UTC)
    picdiff = timedelta(seconds=60*60*1)
    for up in uploads:
        saved_data.append({"deviceId": up.deviceId, "serverDatetime": up.serverDatetime, "recordDatetime": up.recordDatetime,
                           "processing_sucess": up.processing_success(), "processing_results_str": up.processing_result_str(),
                           "misc": up.misc})
        allmisc = json.loads(up.misc)
        allcolumns.extend(allmisc.keys())
        tempset = set(allcolumns)
        allcolumns = list(tempset)
    response['Content-Disposition'] = 'attachment; filename=%s_%s_%s.csv' % (deploymentId, start.strftime("%Y%m%d"), stop.strftime("%Y%m%d"))
    headerstr = "deviceId,serverDatetime,recordDatetime,success,load,conc,"
    for col in allcolumns:
        headerstr += col + ","
    response.write(headerstr + "\n")
    for row in saved_data:
        log.info("%s %s %s" % (str(row['recordDatetime']), str(prevdate), str(row['recordDatetime'] - prevdate)))
        if row['recordDatetime'] - prevdate > picdiff:
            outstr  = "skip,,,,,,,,,,,,1.1.22,1.1.23\n"
            outstr += "skip,,,,,,,,,,,,1.1.22,1.1.23\n"
            outstr += "skip,,,,,,,,,,,,1.1.22,1.1.23\n"
            outstr += "skip,,,,,,,,,,,,1.1.22,1.1.23\n"
            outstr += "skip,,,,,,,,,,,,1.1.22,1.1.23\n"
            response.write(outstr)
            outstr = ""
        prevdate = row['recordDatetime']
        outstr = row['deviceId'] + "," + str(row['serverDatetime']) + "," + str(row['recordDatetime']) + "," + yesno(row['processing_sucess']) + "," + row['processing_results_str'] + ","
        misc = json.loads(row['misc'])
        for col in allcolumns:
            if misc.has_key(col):
                outstr += str(misc[col]) + ","
            else:
                outstr += ","
        outstr += "\n"
        response.write(outstr)
    return response



@login_required
def data_download(request, deploymentId):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))
    start = None
    stop = None
    
    response = HttpResponse(mimetype='text/csv')
    if request.method == 'POST':
        form = DownloadDataForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data['startDateTime']
            stop = form.cleaned_data['stopDateTime']
        else:
            start = datetime.strptime(request.POST['startDateTime'], '%m/%d/%Y')
            stop = datetime.strptime(request.POST['stopDateTime'], '%m/%d/%Y')
            log.debug("Form is invalid")

    log.debug("Got dates %s %s" % (str(start), str(stop)))
    if start == None or stop == None:
        return response
        
    uploads = SuryaUploadData.objects(Q(deploymentId = deploymentId) & Q(serverDatetime__gte = start) & Q(serverDatetime__lte = stop)).order_by('-serverDatetime')

    saved_data = [];
    allcolumns = [];
    for up in uploads:
        saved_data.append({"deviceId": up.deviceId, "serverDatetime": up.serverDatetime,
                           "processing_sucess": up.processing_success(),
                           "validresult": validresult(up), "processing_results_str": up.processing_result_str(),
                           "misc": up.misc})
        allmisc = json.loads(up.misc)
        allcolumns.extend(allmisc.keys())
        tempset = set(allcolumns)
        allcolumns = list(tempset)
    response['Content-Disposition'] = 'attachment; filename=%s_%s_%s.csv' % (deploymentId, start.strftime("%Y%m%d"), stop.strftime("%Y%m%d"))
    headerstr = "deviceId,serverDatetime,success,valid,load,conc,"
    for col in allcolumns:
        headerstr += col + ","
    response.write(headerstr + "\n")
    for row in saved_data:
        outstr = row['deviceId'] + "," + str(row['serverDatetime']) + "," + yesno(row['processing_sucess']) + "," + row['validresult'] + "," + row['processing_results_str'] + ","
        misc = json.loads(row['misc'])
        for col in allcolumns:
            if misc.has_key(col):
                outstr += str(misc[col]) + ","
            else:
                outstr += ","
        outstr += "\n"
        response.write(outstr)
    return response



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


@login_required
def data_download_day(request, deploymentId, year, month, day):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))

    byrecord = True
    if request.GET.has_key('byrecord'):
        if request.GET.get('byrecord') == "False":
            byrecord = False

    response = HttpResponse(mimetype='text/csv')

    start = datetime(year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC)
    stop = start + timedelta(days=1)
    uploads = None

    if byrecord:
        uploads = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(recordDatetime__gte = start) & Q(recordDatetime__lte = stop)).order_by('+recordDatetime')
    else:
        uploads = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(serverDatetime__gte = start) & Q(serverDatetime__lte = stop)).order_by('+recordDatetime')
    
    saved_data = [];
    allcolumns = [];
    prevdate = datetime.now(pytz.UTC)
    picdiff = timedelta(seconds=60*60*1)
    for up in uploads:
        res_t = SuryaIANAResult.objects(item=up)
        if len(res_t) == 0:
            continue
        res = res_t[0]
        sampled = res.preProcessingResult.sampled
        grads = zip(*res.preProcessingResult.gradient)
        saved_data.append({"deviceId": up.deviceId, "serverDatetime": up.serverDatetime, "recordDatetime": up.recordDatetime,
                           "processing_sucess": up.processing_success(), "processing_results_str": up.processing_result_str(),
                           "misc": up.misc, "sampled": sampled, "grads": grads, "id": up.id})
        allmisc = json.loads(up.misc)
        allcolumns.extend(allmisc.keys())
        tempset = set(allcolumns)
        allcolumns = list(tempset)
    
    response['Content-Disposition'] = 'attachment; filename=%s_%s_%s.csv' % (deploymentId, start.strftime("%Y%m%d"), stop.strftime("%Y%m%d"))
    headerstr = "deviceId,serverDatetime,recordDatetime,success,load,conc,"
    for col in allcolumns:
        headerstr += col + ","
    headerstr += "r,g,b,r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,g0,g1,g2,g3,g4,g5,g6,g7,g8,g9,g10,g11,b0,b1,b2,b3,b4,b5,b6,b7,b8,b9,b10,b11,url"
    response.write(headerstr + "\n")
    for row in saved_data:
        #log.info("%s %s %s" % (str(row['recordDatetime']), str(prevdate), str(row['recordDatetime'] - prevdate)))
        outstr = row['deviceId'] + "," + str(row['serverDatetime']) + "," + str(row['recordDatetime']) + "," + yesno(row['processing_sucess']) + "," + row['processing_results_str'] + ","
        misc = json.loads(row['misc'])
        for col in allcolumns:
            if misc.has_key(col):
                outstr += misc[col] + ","
            else:
                outstr += ","
        sampled = row['sampled']
        grads = row['grads']
        outstr += str(sampled[0]) + "," + str(sampled[1]) + "," + str(sampled[2]) + ","
        for grad in grads:
            for c in grad:
                outstr += str(c) + ","
        outstr += "http://surya.nexleaf.org/surya/" + reverse("view_upload", args=[deploymentId, str(row["id"])])
        outstr += "\n"
        response.write(outstr)
    return response


@login_required
def data_plot_grads_day(request, deploymentId, year, month, day):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))

    byrecord = True
    if request.GET.has_key('byrecord'):
        if request.GET.get('byrecord') == "False":
            byrecord = False
    
    start = datetime(year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC)
    stop = start + timedelta(days=1)
    uploads = None

    if byrecord:
        uploads = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(recordDatetime__gte = start) & Q(recordDatetime__lte = stop)).order_by('+recordDatetime')
    else:
        uploads = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(serverDatetime__gte = start) & Q(serverDatetime__lte = stop)).order_by('+recordDatetime')

    thedate = []
    thedata = {0:[], 1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[], 8:[], 9:[], 10:[], 11:[]}
    sampled = []
    for up in uploads:
        res_t = SuryaIANAResult.objects(item=up)
        if len(res_t) == 0:
            continue
        res = res_t[0]
        thedate.append(up.recordDatetime)
        sampled.append(res.preProcessingResult.sampled[0])
        grad = zip(*res.preProcessingResult.gradient)[0]
        for g in range(len(grad)):
            thedata[g].append(grad[g])
    
    from SuryaWebPortal.utils.plot_loads import *
    response = HttpResponse(mimetype='image/png')
    plot_grads(response, start, thedate, thedata, sampled)
    return response

    

@login_required
def data_plot_load_day(request, deploymentId, year, month, day):
    if not request.user.is_superuser:
        u = MyUser.objects.get(id=request.user.id)
        if deploymentId not in u.deployment_list():
            return HttpResponseRedirect(reverse('SuryaWebPortal.views.home.home'))

    byrecord = True
    if request.GET.has_key('byrecord'):
        if request.GET.get('byrecord') == "False":
            byrecord = False 

    start = datetime(year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC)
    stop = start + timedelta(days=1)
    uploads = None
    if byrecord:
        uploads = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(recordDatetime__gte = start) & Q(recordDatetime__lte = stop)).order_by('+recordDatetime')
    else:
        uploads = SuryaUploadData.objects(Q(deploymentId=deploymentId) & Q(serverDatetime__gte = start) & Q(serverDatetime__lte = stop)).order_by('+recordDatetime')
    
    alldata = {}
    #dates = []
    #loads = []
    #devs = []
    maxload = 0.0
    for up in uploads:
        allmisc = json.loads(up.misc)
        dev = "other"
        if allmisc.has_key('device'):
            dev = allmisc['device']
        if alldata.has_key(dev) is False:
            alldata[dev] = {'dates': [], 'loads': [], 'notes': []}
        res = SuryaIANAResult.objects(item=up)
        alldata[dev]['dates'].append(up.recordDatetime)
        load = 0.0
        if res.count() >= 1:
            load = res[0].computationResult.result.BCAreaRed
        alldata[dev]['loads'].append(load)
        if allmisc.has_key('notes'):
            alldata[dev]['notes'].append(allmisc['notes'])
        else:
            alldata[dev]['notes'].append('')
        #if load > maxload:
        #    maxload = load
    
    from numpy import average
    allmeans = []
    meandates = []
    notesets = []
    timebreak = timedelta(minutes=10)
    imgrpl = re.compile("image")
    numrpl = re.compile("\d+")
    for dev in alldata.keys():
        runmean = []
        rundate = None
        runnotes = []
        prevdate = alldata[dev]['dates'][0]
        rundate = alldata[dev]['dates'][0]
        for i in range(len(alldata[dev]['dates'])):
            if alldata[dev]['dates'][i] - prevdate > timebreak:
                meandates.append(prevdate)
                allmeans.append(average(runmean))
                notesets.append(set(runnotes))
                runmean = []
                rundate = alldata[dev]['dates'][i]
                runnotes = []
            runmean.append(alldata[dev]['loads'][i])
            prevdate = alldata[dev]['dates'][i]
            runnotes.extend(numrpl.sub('', imgrpl.sub('', alldata[dev]['notes'][i])).strip().split())
        meandates.append(prevdate)
        allmeans.append(average(runmean))
        notesets.append(set(runnotes))

    from SuryaWebPortal.utils.plot_loads import *

    response = HttpResponse(mimetype='image/png')

    plot_loads_devs(response, start, alldata, allmeans, meandates, maxload, notesets)

    return response
