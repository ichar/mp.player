#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# Admin model classes
#
# Checked: 2016/10/28
# ichar@g2.ru
#
import copy
import settings

from django import forms, template
from django.db import models
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404, render_to_response

from models import *
from forms import *

#
# =================================================================================================
#

class BaseAdmin( admin.ModelAdmin ):
    """
        The Django admin site.
        Look at "Django  The Django admin site  Django Documentation.mht".
    """
    list_per_page  =  10
    save_as        =  True
    save_on_top    =  True
    save_on_bottom =  False
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

    def render_change_form( self, request, context, add=False, change=False, form_url='', obj=None ):
        opts = self.model._meta
        app_label = opts.app_label
        ordered_objects = opts.get_ordered_objects()
        context.update({
            'add': add,
            'change': change,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'has_delete_permission': self.has_delete_permission(request, obj),
            'has_file_field': True, # FIXME - this should check if form or formsets have a FileField,
            'has_absolute_url': hasattr(self.model, 'get_absolute_url'),
            'ordered_objects': ordered_objects,
            'form_url': mark_safe(form_url),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
            'save_on_bottom': self.save_on_bottom,
            'root_path': self.admin_site.root_path,
        })
        return render_to_response(self.change_form_template or [
            "admin/%s/%s/change_form.html" % (app_label, opts.object_name.lower()),
            "admin/%s/change_form.html" % app_label,
            "admin/change_form.html"
        ], context, context_instance=template.RequestContext(request))

    def list_media( self ):
        from django.conf import settings
        from django import forms
        #js = [ 'js/jquery-1.4.1.min.js', 'js/common.js', 'js/job.updater.js' ] # http://code.jquery.com/jquery-latest.js
        js = [ 'js/job.updater.js' ]
        if settings.ENABLE_ITEM_BACKGROUND:
            js.append('js/item.links.js')
        return forms.Media(js=['%s%s' % (not url.startswith('http') and settings.ADMIN_MEDIA_PREFIX or '', url) for url in js])
    list_media = property(list_media)

    def extra_html( self ):
        return ''
    extra_html = property(extra_html)


class CompanyAdmin( BaseAdmin ):
    """
        *Company* admin
    """
    fieldsets = [
        (_('Country'), {
                'fields'  : [
                    'country',
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('table',)}
            }),
        (_('Title & Description'), {
                'fields'  : [
                    'title', 
                    'name', 
                    'code', 
                    'description',
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table',)}
            }),
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom', 'collapse'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'rendered_name', 'rendered_description', 'rendered_country', ) #, 'rendered_RD'
    list_filter   = ('country', )
    ordering      = ('title', )
    search_fields = ('title', 'code', 'description', )

    list_display_links  = ('title', )
    list_per_page = settings.LIST_PER_PAGE_DEFAULT

    filter_panel_width = '150px'
    change_list_style = 'width:100%;'

    form = CompanyForm

class BranchAdmin( BaseAdmin ):
    """
        *Branch* admin
    """
    fieldsets = [
        (_('Company'), {
                'fields' : [
                    'company', 
                    'type', 
                    'code', 
                    'IsHeadOffice',
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table',)}
            }),
        (_('Title & Description'), {
                'fields' : [
                    'title', 
                    'country', 'postcode',
                    'city',
                    'address',
                    'phone1', 
                    'phone2', 
                    'fax',
                    'email',
                ], 
                'classes' : ['custom'],
                'options' : {'layouts' : ('table', 'div', 'div', 'div', 'div', 'div', 'div', 'div', 'table',)}
            }),
        (_('PayStructure & MYOB'), {
                'fields' : [
                    'pay', 
                    'account', 
                    'department',
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('div', 'div', 'div',)}
            }),
        (_('Notes'), {
                'fields' : [
                    'notes'
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('table',)}
            }),
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom', 'collapse'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'rendered_company', 
                     'rendered_phones', 'rendered_fax', 'rendered_email', 'rendered_country', 'rendered_city',
                     'rendered_HO', ) #, 'rendered_RD'
    list_filter   = ('type', 'company', 'country', 'city', 'department', )
    ordering      = ('title', 'company', )
    search_fields = ('title', 'code', 'city', 'address', 'phone1', 'phone2', 'fax', 'email', 'company__title', )

    list_display_links  = ('title', )
    list_per_page = 30 #settings.LIST_PER_PAGE_DEFAULT

    filter_panel_width = '220px'
    change_list_style = 'width:100%;'

    form = BranchForm

class ContactAdmin( BaseAdmin ):
    """
        *Contact* admin
    """
    fieldsets = [
        (_("Company's Branch (Client)"), {
                'fields' : [
                    'company', 
                    'branch',
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('table', 'table',)}
            }),
        (_('Title & Description'), {
                'fields'  : [
                    'title',
                    'name',
                    'phone', 
                    'mobile',
                    'email',
                    'notes',
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('table', 'table', 'div', 'div', 'table', 'table')}
            }),
        (_('Misc'), {
                'fields'  : [
                    'salutation',
                    'IsManager',
                ], 
                'classes' : ['custom'],
                'options' : {'layouts' : ('table', 'table', 'table')}
            }), 
        (_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom', 'collapse'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('title', 'rendered_branch', # 'rendered_salutation', 
                     'rendered_phone', 'rendered_mobile', 'rendered_email', 'rendered_city', 
                     'rendered_OM', ) # 'rendered_RD'
    list_filter   = ('company', 'branch', 'salutation', 'IsManager', )

    ordering      = ('title', )
    search_fields = ('title', 'name', 'phone', 'mobile', 'email', 'branch__city', 'notes',)

    list_display_links  = ('title', )
    list_per_page = 100# settings.LIST_PER_PAGE_DEFAULT

    filter_panel_width = '245px'
    change_list_style = 'width:100%;'

    form = ContactForm

class JobAdmin( BaseAdmin ):
    """
        *Job* admin
    """
    fieldsets = [
        (_('Client'), {
                'fields' : [
                    'company', 
                    'branch', 
                    'contact', 
                   #'code',
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table',)}
            }),
        (_('Title & Description'), {
                'fields'  : [
                    'title',
                    'received', 
                   ('default', 'price',),
                    'calculated',
                   ('amend_total', 'amendments',),
                    'status',
                    'user',
                    'notes',
                   ('IsAmendment', 'IsArchive',),
                ],
                'classes' : ['custom'],
                'options' : {'layouts' : ('div', 'div', 'div', 'div', 'div', 'div', 'div', 'div', 'box:edged')}
            }),
        (_('Details'), {
                'fields'  : [
                    'type',
                    'property',
                    'square',
                    'runtime',
                    'finished', 
                ],
                'classes' : ['custom', 'collapse'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table', 'table', 'table',)}
            }),
        #(_('Registry Date'), {'fields' : ['RD'], 'classes' : ['custom', 'collapse'], 'options' : {'layouts' : ('table',)}}),
    ]

    list_display  = ('rendered_received', 'rendered_status', 'rendered_AC', 'rendered_AR', 
                     'rendered_job', 'rendered_title', 
                     'rendered_phones', 'rendered_user', 'rendered_amendments', 
                     'notes',
                     )
                     #'CDT', 'RT',
                     #'rendered_property', 'rendered_square', 'rendered_prices', 
                     #'rendered_amend_total', 'rendered_RD', 'rendered_finished',
                     #'rendered_default'
    list_filter   = ('status', 'IsAmendment', 'IsArchive', 'user', 'company',
                    ('branch', ('company__id__exact',),), ('contact', ('company__id__exact', 'branch__id__exact',),),) #'branch', 'contact', 
    ordering      = ('-received', ) # '-RD' '-calculated' 
    search_fields = ('title', 'code', 
                     'company__title', 'company__code', 'company__description', #'company__country__title' # !!! error (not allowed),
                     'branch__title', 'branch__email', 'branch__phone1', 'branch__phone2', 'branch__fax', 'branch__notes',
                     'contact__title', 'contact__email', 'contact__phone', 'contact__mobile', 'contact__notes', 
                     ) # '^company'

    list_display_links  = ('rendered_title',)

    date_hierarchy = 'received'
    list_per_page = 30 #settings.LIST_PER_PAGE_DEFAULT

    filter_panel_width = '252px'
    change_list_style = 'width:100%;'

    form = JobForm

    def extra_html( self ):
        from references.models import Status
        output = ''
        html = """
<tr>
<td class="new_status_value"><input type="radio" id="status_id_%(pk)s" name="new_status" value="%(pk)s"></td>
<td class="new_status_title" nowrap><label id="status_title_%(pk)s" for="status_id_%(pk)s">%(title)s</label></td>
</tr>
"""
        output += '<div id="new_status_container"><table border="0">%s</table></div>\n' % \
                  ''.join([html % {'pk':x.pk, 'title':x.title.replace('!', '').strip()} for x in Status.objects.all().order_by('title')]
                )
        html = """
<tr>
<td class="new_user_value"><input type="radio" id="user_id_%(pk)s" name="new_user" value="%(pk)s"></td>
<td class="new_user_title" nowrap><label id="user_title_%(pk)s" for="user_id_%(pk)s">%(title)s</label></td>
</tr>
"""
        output += '<div id="new_user_container"><table border="0">%s</table></div>\n' % \
                  ''.join([html % {'pk':x.pk, 'title':x.username} for x in User.objects.all().order_by('username') \
                        if x.is_active and x.username not in ('admin',)]
                )
        html = """
<td nowrap><input type="button" class="new_mail_button" onclick="javascript:confirmMail(%(pk)s);" value="%(title)s"></td>"""
        mail_status = settings.MAIL_STATUS_LIST + [( 0, 'Simple mail', ), ( -1, 'Cancel', )]
        output += '<div align="center" id="new_mail_container"><table border="0"><tr><td colspan="%s" class="new_mail_header">%s</td></tr><tr>%s</tr></table></div>\n' % ( \
                   len(mail_status), 
                  "<strong>You can change the given Job status to indicate one's current state or send simple mail.</strong><div id=\"mail_address\">xxx</div>Please, select your choice.",
                  ''.join([html % {'pk':x[0], 'title':x[1]} for x in mail_status]),
                )
        return output
    extra_html = property(extra_html)


admin.site.register( Company, CompanyAdmin )
admin.site.register( Branch,  BranchAdmin  )
admin.site.register( Contact, ContactAdmin )
admin.site.register( Job,     JobAdmin     )
