#!/usr/bin/python

from django.conf import settings
from django import template

from Validation import Validate
from Collections.SuryaProcessResult import *



# COMMON TAGS - Used sitewide.
# IMPORTANT - These are loaded "globally" - via SeabirdDataPortal/__init__.py add_to_builtins
register = template.Library()

# Determine if tab is active
@register.simple_tag
def validresult(upload):
    res = SuryaIANAResult.objects(item=upload)
    if res == None or len(res) == 0:
        return ''
    warn, warnmsg = Validate.validate(res[0])
    if warn == True:
        return ''
    elif warn == False:
        return '<b>Yes</b>'
    else:
        return 'Unknwn'
