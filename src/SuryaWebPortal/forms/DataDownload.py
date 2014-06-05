#!/usr/bin/python


import logging
from Logging.Logger import getLog
from django import forms


log = getLog('forms')
log.setLevel(logging.DEBUG)


class DownloadDataForm(forms.Form):
    startDateTime = forms.DateField(required=True, label='Start Date',
                                    widget=forms.DateInput(attrs={'class':'date_picker'}, format='%m/%d/%Y'))
    stopDateTime = forms.DateField(required=True, label='Stop Date',
                                   widget=forms.DateInput(attrs={'class':'date_picker'}, format='%m/%d/%Y'))
    
    def __init__(self, *args, **kwards):
        super(DownloadDataForm, self).__init__(*args, **kwards)
        #self.fields['deviceId'].choices = [ (d.deviceId, "%-10s - %s" % (str(d.deviceName), d.deviceId)) for d in DeviceData.objects ]

    def clean_startDateTime(self):
        try:
            d = self.cleaned_data['startDateTime']
            dt = datetime(d.year, d.month, d.day)
            self.cleaned_data['startDateTime'] = dt
            print "now is " + str(self.cleaned_data)
            return dt
        except:
            raise forms.ValidationError("Invalid Start Date.")
        return None
    
    def clean_stopDateTime(self):
        try:
            d = self.cleaned_data['stopDateTime']
            dt = datetime(d.year, d.month, d.day)
            self.cleaned_data['stopDateTime'] = dt
            return dt
        except:
            raise forms.ValidationError("Invalid Stop Date.")
        return None
        
    #def clean_deviceId(self):
    #    device_id = self.cleaned_data['deviceId']
    #    try:
    #        deviceId = DeviceData.objects.get(deviceId=device_id)
    #        self.cleaned_data['deviceId'] = deviceId
    #        return deviceId
    #    except:
    #        raise forms.ValidationError("Invalid Device Selected.")
    #    return device_id
