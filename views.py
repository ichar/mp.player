#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# Views.
#
# Checked: 2010/03/31
# ichar@g2.ru
#
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse

from django.shortcuts import render_to_response
import datetime

def thanks(request):
    return render_to_response('thanks.html', locals())

