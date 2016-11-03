#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# References. Admin model classes
#
# Checked: 2010/05/03
# ichar@g2.ru
#
import copy
from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from models import *
from forms import *

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
        #print 'save_model: %s' % `self`

    def save_formset( self, request, form, formset, change ):
        """
        Given an inline formset save it to the database.
        """
        formset.save()
        #print 'save_formset: %s' % `self`

    #def list_media( self ):
    #    return ''
    #list_media = property(list_media)

    def list_media( self ):
        from django.conf import settings
        from django import forms
        js = []
        if settings.ENABLE_ITEM_BACKGROUND:
            js.append('js/item.links.js')
        return forms.Media(js=['%s%s' % (not url.startswith('http') and settings.ADMIN_MEDIA_PREFIX or '', url) for url in js])
    list_media = property(list_media)

    def extra_html( self ):
        return ''
    extra_html = property(extra_html)

class CountryAdmin( BaseAdmin ):
    """
        *Country* admin
    """
    fieldsets = [
        (_('Title & Description'), {
                'fields' : [
                    'title',
                ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('table',)},
            }),
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'rendered_RD', )
    ordering      = ('title',)
    search_fields = ('title',)

    form = CountryForm

class DepartmentAdmin( BaseAdmin ):
    """
        *Department* admin
    """
    fieldsets = [
        (_('Title & Description'), {
                'fields'  : [
                    'title',
                ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('table',)},
            }),
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'rendered_RD',)
    ordering      = ('title',)
    search_fields = ('title',)

    form = DepartmentForm

class StatusAdmin( BaseAdmin ):
    """
        *Status* admin
    """
    fieldsets = [
        (_('Title & Description'), {
                'fields'  : [
                   ('title', 'type', 'structure', 'sortkey',),
                ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('table',)},
            }),
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'type', 'rendered_RD', ) # , 'sortkey'
    list_filter   = ('type', )
    ordering      = ('title', ) # 'sortkey',
    search_fields = ('title', 'type', )

    list_display_links  = ('title', )

    form = StatusForm

class PayStructureAdmin( BaseAdmin ):
    """
        *PayStructure* admin
    """
    fieldsets = [
        (_('Title & Description'), {
                'fields'  :  [
                    'title', 
                    'type', 
                   #'code',
                    'fixed_fee', 
                    'amendments',
                ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('table', 'table', 'table', 'table', 'table',)},
            }),
        (_('Pay Structure'), {
                'fields'  :  [
                    ('price1', 'price2', 'price3', 'price4', 'price5', 'price6', 'price7', 'price8', 'price9', 'price10',),
                    ('max1', 'max2', 'max3', 'max4', 'max5', 'max6', 'max7', 'max8', 'max9', 'max10',),
                    ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('div', 'div',)},
            }),
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'rendered_type', 'fixed_fee', 'rendered_amendments', 'price1', 'max1', 'rendered_RD', )
    list_filter   = ('type', )
    ordering      = ('title', )
    search_fields = ('title', 'type', 'code', )

    filter_panel_width = '150px'
    change_list_style = 'width:850px;'

    form = PayStructureForm

class MYOBAdmin( BaseAdmin ):
    """
        *MYOB* admin
    """
    fieldsets = [
        (_('Title & Description'), {
                'fields'  : [
                    'title', 
                    'type',
                   #'code',
                ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('table', 'table', 'table',)},
            }),
        (_('MYOB Information'), {
                'fields'  :  [
                   ('myobcompany', 'myobaccount', 'myobvat', 'myobquantity',),
                ],
                'classes' :  ['custom'],
                'options' :  {'layouts' : ('table',)},
            }),
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'rendered_type', 'myobcompany', 'myobaccount', 'myobvat', 'myobquantity', 'rendered_RD', )
    list_filter   = ('type', )
    ordering      = ('title', )
    search_fields = ('title', 'type', 'code', )

    filter_panel_width = '150px'
    change_list_style = 'width:850px;'

    form = MYOBForm


admin.site.register( Country,      CountryAdmin )
admin.site.register( Department,   DepartmentAdmin )
admin.site.register( Status,       StatusAdmin )
admin.site.register( PayStructure, PayStructureAdmin )
admin.site.register( MYOB,         MYOBAdmin )
