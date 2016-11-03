#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# jobs/views.py
#
# Checked: 2016/10/20
# ichar@g2.ru
#
import datetime
from settings import EMAILED_STATUS_ID
from utils import print_exception

from django.db.models import Q
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core import serializers
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.utils.html import escape, linebreaks, conditional_escape

from jobs.flowlogic import JobFlowLogic
from jobs.exporter import ExcelReport
from jobs.models import Company, Branch, Contact, PayStructure, MYOB, Job
from references.models import Status
from jobs.forms import FeedbackForm

def search( request ):
    #
    # Returns search page view
    #
    query = request.GET.get('query', '')

    if query:
        qset = (
            Q(title__icontains=query) |
            Q(authors__first_name__icontains=query) |
            Q(authors__last_name__icontains=query)
        )
        results = Client.objects.filter(qset).distinct()
    else:
        results = []
    return render_to_response('jobs/search.html', {
            "results" : results,
            "query"   : query
        },
    )

def feedback( request ):
    #
    # Returns feedback page view
    #
    initial = {'sender': 'user@example.com'}

    if request.method == 'POST':
        form = FeedbackForm(request.POST, initial=initial)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            message = form.cleaned_data['message']
            sender = form.cleaned_data.get('sender', 'noreply@example.com')
            send_mail(
                'Feedback from your site, topic: %s' % topic,
                message, sender,
                ['ichar@g2.ru']
            )
            return HttpResponseRedirect('/thanks/')
    else:
        form = FeedbackForm(initial=initial)

    return render_to_response('jobs/feedback.html', { 'form': form })

def myob_to_excel( request ):
    # use a StringIO buffer rather than opening a file
    import csv
    from StringIO import StringIO

    output = StringIO()
    w = csv.writer(output)
    for i in range(10):
        w.writerow(range(10))
    # rewind the virtual file
    output.seek(0)
    return HttpResponse(output.read(), mimetype='application/ms-excel')

def tracker( request ):
    mode = request.POST.get('mode', None)
    id = request.POST.get('id', None)
    value = request.POST.get('value', None)
    author = request.POST.get('author', None)
    results = None

    try:
        if not mode:
            pass

        elif id is not None and mode == 'notes':
            ob = Job.objects.get(id=id)
            if ob is not None:
                if value:
                    ob.notes = conditional_escape(escape(value))
                    value = '%s' % linebreaks(ob.notes)
                else:
                    ob.notes = value = ''
                ob.save()
                log_change( request, ob, author, "Notes was changed by [%s]: %s." % (author, value) )

        else:
            value = ''

    except:
        print_exception()

    return HttpResponse(value, mimetype='text/plain')

def loader( request ):
    #
    # Ajax Data Loader (ForeignKey updater)
    #
    # >>> from django.contrib.auth.models import Group
    # >>> from django.core import serializers
    # >>> print serializers.serialize('json', Group.objects.all(), indent=4)
    #
    mode = request.GET.get('mode', None)
    id = request.GET.get('id', None)
    value = request.GET.get('value', None)
    author = request.GET.get('author', None)
    results = None

    try:
        if not mode:
            pass

        elif mode == 'time':
            now = datetime.datetime.now()
            sec = str(now.second)
            results = [ \
                '%s-%s-%s' % (now.year, ('0'+str(now.month))[-2:], ('0'+str(now.day))[-2:]),
                '%s:%s' % (('0'+str(now.hour))[-2:], ('0'+str(now.minute))[-2:]),
                ('0'+sec)[-2:],
            ]
            return HttpResponse('#'.join(results), mimetype='text/plain')

        elif id is not None and mode == 'AMD':
            id = id.split('_')[1]
            ob = Job.objects.get(id=id)
            value = ''
            if ob is not None:
                ob.amendments += 1
                ob.IsAmendment = True
                value = '%s' % ob.amendments
                ob.save()
                log_change( request, ob, author, "Amendments Count was changed by [%s]: %s." % (author, value) )
            return HttpResponse(value, mimetype='text/plain')

        elif id is not None and mode in ('company2branches', 'company2contacts', 'branch2contacts',):
            if not mode or mode == 'company2branches':
                results = [( x.id, x.title, ) for x in Branch.objects.filter(company=id).distinct()]
            elif mode == 'company2contacts':
                results = [( x.id, x.title, ) for x in Contact.objects.filter(company=id).distinct()]
            elif mode == 'branch2contacts':
                results = [( x.id, x.title, ) for x in Contact.objects.filter(branch=id).distinct()]
            return render_to_response('jobs/loader.html', {'results': tuple(results)})

        elif mode == 'check_status':
            x, id, old_status = id.split('_')
            ob = Job.objects.get(id=id)
            return HttpResponse(str(ob.status.id) != old_status and '1' or '', mimetype='text/plain')

        elif mode == 'change_status':
            id = id.split('_')[1]
            message = request.GET.get('message', None)
            ob = Job.objects.get(id=id)
            status = Status.objects.get(id=value)
            if ob is not None and status is not None:
                ob.status = status
                if value.isdigit() and int(value) == EMAILED_STATUS_ID:
                    ob.finished = datetime.datetime.now()
                ob.save()
            ob = Job.objects.get(id=id)
            if ob is not None:
                results = [ Status.objects.get(id=ob.status.id) ]
                log_change( request, ob, author, "Status was changed by [%s]: %s." % (message, ob.status.title) )
            return HttpResponse(serializers.serialize('json', results), mimetype='application/json')

        elif mode == 'change_user':
            id = id.split('_')[1]
            ob = Job.objects.get(id=id)
            user = User.objects.get(id=value)
            if ob is not None and user is not None:
                ob.user = user
                ob.save()
            ob = Job.objects.get(id=id)
            if ob is not None:
                results = [ User.objects.get(id=ob.user.id) ]
                log_change( request, ob, author, "Drawn by was changed: %s." % ob.user.username )
            return HttpResponse(serializers.serialize('json', results), mimetype='application/json')

        elif mode == 'company2wizard':
            try:
                results = [ Company.objects.get(id=id) ]
            except:
                results = []
            return HttpResponse(serializers.serialize('json', results), mimetype='application/json')

        elif mode == 'branch2wizard':
            try:
                results = [ Branch.objects.get(id=id) ]
            except:
                results = []
            return HttpResponse(serializers.serialize('json', results), mimetype='application/json')

        elif mode == 'contact2wizard':
            try:
                results = [ Contact.objects.get(id=id) ]
            except:
                results = []
            return HttpResponse(serializers.serialize('json', results), mimetype='application/json')

        elif mode == 'paystructure2wizard':
            try:
                results = [ PayStructure.objects.get(id=id) ]
            except:
                results = []
            return HttpResponse(serializers.serialize('json', results), mimetype='application/json')

        elif mode == 'myob2wizard':
            try:
                results = [ MYOB.objects.get(id=id) ]
            except:
                results = []
            return HttpResponse(serializers.serialize('json', results), mimetype='application/json')

        elif mode == 'job2wizard':
            try:
                results = [ Job.objects.get(id=id) ]
            except:
                results = []
            return HttpResponse(serializers.serialize('json', results), mimetype='application/json')

        elif mode == 'report2columns':
            return ExcelReport().render(request, context={'loader':1})

    except:
        print_exception()

    return HttpResponse(results, mimetype='text/plain')

def flow_client_loader( request ):
    from django.contrib import admin
    mode = 'action' in request.GET and 'flow-client-action' or 'flow-client-search'
    return JobFlowLogic(admin.site).render( request, mode )

def flow_paystructure_loader( request ):
    from django.contrib import admin
    return JobFlowLogic(admin.site).render( request, 'flow-paystructure-item' )

def flow_job_loader( request ):
    from django.contrib import admin
    mode = 'action' in request.POST and 'flow-job-action' or 'pk__exact' in request.GET and 'flow-job-item' or 'flow-job-search'
    return JobFlowLogic(admin.site).render( request, mode )

def log_change( request, object, author, message ):
    # Add changed item info to AdminLog
    from django.contrib.admin.models import LogEntry, CHANGE
    try:
        user = User.objects.get(username=author)
    except:
        return
    if user is None:
        return
    LogEntry.objects.log_action(
        user_id         = user.pk, 
        content_type_id = ContentType.objects.get_for_model(object).pk, 
        object_id       = object.pk, 
        object_repr     = force_unicode(object), 
        action_flag     = CHANGE, 
        change_message  = message
    )
