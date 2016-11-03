#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# utils.py
#
# Checked: 2016/10/20
# ichar@g2.ru
#
import sys
import datetime
import traceback
from types import ListType, TupleType

from settings import IsDeepDebug, errorlog, LOCAL_FULL_TIMESTAMP

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.utils.encoding import force_unicode
from django.utils.text import capfirst, get_text_list

cr = '\n'

def has_add_permission( request, klass ):
    # Returns True if the given request has permission to add an object 
    opts = klass._meta
    return request.user.has_perm(opts.app_label + '.' + opts.get_add_permission())

def has_change_permission( request, klass ):
    # Returns True if the given request has permission to add change the given object
    opts = klass._meta
    return request.user.has_perm(opts.app_label + '.' + opts.get_change_permission())

def log_addition( request, object, message ):
    # Log that an object has been successfully added. 
    # The default implementation creates an admin LogEntry object.
    if object is None:
        return
    from django.contrib.admin.models import LogEntry, ADDITION
    LogEntry.objects.log_action(
        user_id         = request.user.pk, 
        content_type_id = ContentType.objects.get_for_model(object).pk,
        object_id       = object.pk,
        object_repr     = force_unicode(object), 
        action_flag     = ADDITION,
        change_message  = message
    )
    
def log_change( request, object, message ):
    # Log that an object has been successfully changed. 
    # The default implementation creates an admin LogEntry object.
    if object is None:
        return
    from django.contrib.admin.models import LogEntry, CHANGE
    LogEntry.objects.log_action(
        user_id         = request.user.pk, 
        content_type_id = ContentType.objects.get_for_model(object).pk, 
        object_id       = object.pk, 
        object_repr     = force_unicode(object), 
        action_flag     = CHANGE, 
        change_message  = message
    )

def construct_change_message( form, client ):
    # Construct a change message from a changed object.
    change_message = []
    changed_data = form._changed_data
    if changed_data is not None:
        x = get_text_list(changed_data, _('and'))
        change_message.append(_('Changed by %s%s.') % (client, x and ': ' + x or '') )
    else:
        change_message.append(_('Added by %s.') % client)
    change_message = ' '.join(change_message)
    return change_message or _('No fields changed.')

def print_traceback( exc_traceback=None ):
    if exc_traceback is None:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if not exc_traceback:
            return ''
    trace = traceback.extract_tb( exc_traceback )
    out = 'Traceback (innermost last):\n'
    for filename, lineno, function, message in trace:
        out += "  File %s, line %s, in %s\n" % ( filename, lineno, function )
        out += "    %s\n" % message
    out += "Customized specially for Express Suite DMS"
    return out

def print_to(f, v, mode='a', request=None):
    items = type(v) not in (ListType, TupleType,) and [v] or v
    fo = open(f, mode=mode)
    for text in items:
        if IsDeepDebug:
            print text
        try:
            if request:
                fo.write('%s--> %s%s' % (cr, request.url, cr))
            fo.write(text)
            fo.write(cr)
        except Exception, error:
            pass
    fo.close()

def print_exception():
    print_to(errorlog, '>>> %s:%s' % (datetime.datetime.now().strftime(LOCAL_FULL_TIMESTAMP), cr))
    traceback.print_exc(file=open(errorlog, 'a'))
