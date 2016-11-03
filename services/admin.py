#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# Services. Admin model classes
#
# Checked: 2011/11/03
# ichar@g2.ru
#
import copy

from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.http import Http404, HttpResponse, HttpResponseRedirect
from manage.models import LogEntry

from models import DebugLog
from forms import DebugLogForm

import patches

#
# =================================================================================================
#

class BaseAdmin( admin.ModelAdmin ):
    """
        The Django admin site.
        Look at "Django  The Django admin site  Django Documentation.mht".
    """
    list_per_page  =  20
    save_as        =  True
    save_on_top    =  False
    date_hierarchy = 'RD'

    list_display_links  = ('title', )
    
    def save_model( self, request, obj, form, change ):
        """
        ModelAdmin methods.
        Given a model instance save it to the database.
        """
        obj.save()

    def save_formset( self, request, form, formset, change ):
        """
        Given an inline formset save it to the database.
        """
        formset.save()

    #def list_media( self ):
    #    return ''
    #list_media = property(list_media)

    def list_media( self ):
        from django.conf import settings
        from django import forms
        js = []
        return forms.Media(js=['%s%s' % (not url.startswith('http') and settings.ADMIN_MEDIA_PREFIX or '', url) for url in js])
    list_media = property(list_media)

    def extra_html( self ):
        return ''
    extra_html = property(extra_html)

class DebugLogAdmin( BaseAdmin ):
    """
        *DebugLog* admin
    """
    fieldsets = [
        (_('Title'), {
                'fields' : [
                    'title',
                    'type', 
                    'user',
                    'IsDone',
                ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('table', 'div', 'table', 'table',)},
            }),
        (_('Description & Comments'), {
                'fields' : [
                    'description',
                ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('table',)},
            }),
        (_('Due Date'), {
                'fields'  : [
                   ('received', 'finished',),
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('table', 'table',)}
            }),
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'rendered_type', 'rendered_description', 'rendered_user', 
                     'rendered_done', 'rendered_received', # 'rendered_finished', 'rendered_RD',
                      )
    list_filter   = ('type', 'user', 'IsDone' )
    ordering      = ('-received',)
    search_fields = ('title', 'description',) # 'user',

    list_per_page  =  7

    filter_panel_width = '220px'
    change_list_style = 'width:100%;'

    form = DebugLogForm

class LogEntryAdmin( admin.ModelAdmin ):
    list_display  = ('rendered_action_time', 'rendered_content_type', 'caption', 'rendered_user', 'rendered_object_id', 
                     'rendered_action', 'rendered_message',) # 'object_repr'
    list_editable = ()
    list_filter   = ('action_time', 'user', 'content_type', 'action_flag')
    ordering      = ('-action_time',)
    search_fields = ('change_message', 'object_id', 'object_repr',) #'user', 
    list_display_links = ('caption',)

    list_per_page  =  20
    date_hierarchy = 'action_time'

    filter_panel_width = '180px'
    change_list_style = 'width:100%;'

    editable = False

class ViewLogEntry( LogEntry ):
    pass

admin.site.register( DebugLog, DebugLogAdmin )
admin.site.register( LogEntry, LogEntryAdmin )
