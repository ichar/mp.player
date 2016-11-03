#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# jobs/wizard.py
#
# Checked: 2010/06/10
# ichar@g2.ru
#
from django import forms
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.contrib.admin.util import quote, unquote, flatten_fieldsets
from django.contrib.admin import widgets

from django.db import models, transaction
from django.forms import ModelChoiceField
from django.forms.forms import BoundField
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.contrib.formtools.wizard import FormWizard
from django.contrib.admin.widgets import AdminSplitDateTime

from jobs.forms import CompanyForm, BranchForm, ContactForm, JobForm
from references.forms import PayStructureForm, MYOBForm, Country
from jobs.models import Job, BRANCH_CHOICES, SALUTATION_CHOICES, PRICE_CHOICES
from references.models import STATUS_TYPE_CHOICES, PAY_CHOICES, MYOB_CHOICES
from widgets import AdvSelect, CountDownTimer
from utils import has_add_permission, log_addition, log_change, construct_change_message

FORMLINES_LIST = ('table', 'div', 'hidden', 'default',)
DATE_FIELDS = ('received', 'finished',)
BOOLEAN_FIELDS = ('IsAmendment', 'IsArchive', 'IsManager', 'IsHeadOffice',)
STEP_FIELD_NAME = "wizard_step"
PK_EMPTY = u'-1'

IsDebug = 0


def _prefix_for_step( step ):
    return str(step) or '0'

def _fieldname_for_step( step, id ):
    return "%s-%s" % ( _prefix_for_step(step), id )

def _form_name( form ):
    return form._meta.model.__name__.lower()


class WizardModel( FormWizard ):
    """
        Wizard model form prototype.
        Model including Form of field as list: Fieldsets -> Fieldline -> Field.
    """
    def get_form( self, step, data=None, request=None ):
        #
        # Helper method that returns the Form instance for the given step
        #
        current_form = self.form_list[step]
        prefix = self.prefix_for_step(step)
        pk_ref = getattr(current_form, 'primary_reference', None)
        pk = ( data is not None and data.get('%s-pk' % prefix) ) or \
             ( request is not None and pk_ref and request.get(pk_ref) ) or None
        #if step==3 and pk_ref: raise 1
        empty_permitted = True
        obj = None

        if pk and pk != PK_EMPTY:
            model = current_form._meta.model
            try:
                obj = model._default_manager.get(pk=pk)
                empty_permitted = False
            except model.DoesNotExist:
                pass

        form = current_form(data, prefix=prefix, #empty_permitted=empty_permitted, 
                initial=self.initial.get(step, None),
                instance=obj
            )

        #del current_form
        #instance = form.instance.__dict__
        #if step == 2: raise 1 # data is not None and
        if IsDebug:
            print "form is OK: step[%s], pk[%s]" % (step, pk)
        return form

    def prefix_for_step( self, step ):
        return _prefix_for_step(step)

    def get_fieldname_for_step( self, step, id ):
        if step is None:
            step = self.step
        return _fieldname_for_step(step, id)

    def custom_is_valid( self, form, request ):
        # Helper function to perform custom form validation
        if not form.is_valid():
            mode = getattr(form, 'custom_validation', [])
            errors = form.errors.keys()
            if mode:
                if 'cooked' in mode:
                    cooked = getattr(form, 'cooked', None) or []
                    if cooked:
                        for i, f, v, s in cooked:
                            if i in errors:
                                del form.errors[i]
            if not form.errors:
                if IsDebug:
                    print "custom valid"
                return 1
            else:
                if IsDebug:
                    print "custom not valid: %s" % form.errors.keys()
                return 0
        return 1

    def determine_step( self, request, *args, **kwargs ):
        if args:
            if 'start' in args:
                return 0
            if 'back' in args:
                if self.step > 0:
                    self.step = self.step - 1
                return self.step
        if not request.POST:
            return 0
        try:
            step = int(request.POST.get(STEP_FIELD_NAME, 0))
        except ValueError:
            return 0
        return step

    def __call__( self, request, *args, **kwargs ):
        #
        # Main method that does all the hard work, conforming to the Django view interface
        # 
        if IsDebug:
            print args

        if not has_add_permission(request, Job):
            raise PermissionDenied

        IsStart = ('start' in args or not request.POST) and 1 or 0
        IsFinish = ('finish' in args or not request.POST) and 1 or 0
        IsBack = 'back' in args and 1 or 0

        if 'extra_context' in kwargs:
            self.extra_context.update(kwargs['extra_context'])
        current_step = self.determine_step(request, *args, **kwargs)
        self.parse_params(request, *args, **kwargs)

        if IsDebug:
            print "call step: %s" % current_step

        # Sanity check.
        if current_step >= self.num_steps():
            raise Http404('Step %s does not exist' % current_step)

        # For each previous step, verify the hash and process.
        # TODO: Move "hash_%d" to a method to make it configurable.
        if not (IsStart or IsBack):
            for i in range(current_step):
                form = self.get_form(i, request.POST)
                #if request.POST.get("hash_%d" % i, '') != self.security_hash(request, form):
                #    return self.render_hash_failure(request, i)
                self.process_step(request, form, i)

        # Process the current step. If it's valid, go to the next step or call
        # done(), depending on whether any steps remain.
        if request.method == 'POST':
            data = request.POST
        else:
            data = None
        form = self.get_form(current_step, data)

        # Start always without any checking
        if IsStart or IsBack:
            if IsDebug:
                print "start:% s" % current_step

        # Only for requested form perform custom validation
        #elif self.custom_is_valid(form, request):
        elif form.is_valid():
            self.process_step(request, form, current_step)
            next_step = current_step + 1

            # If this was the last step, validate all of the forms one more
            # time, as a sanity check, and call done().
            num = self.num_steps()
            if next_step == num or IsFinish:
                #final_form_list = [ self.get_form(i, data) for i in range(num) ]

                # Validate all the forms. If any of them fail validation, that
                # must mean the validator relied on some other input, such as
                # an external Web site.
                #for i, f in enumerate(final_form_list):
                #    if not f.is_valid():
                #        return self.render_revalidation_failure(request, i, f)
                #return self.done(request, final_form_list)
                return self.done(request, current_step)

            # Otherwise, move along to the next step.
            else:
                form = self.get_form(next_step, request=data)
                self.step = current_step = next_step

            if IsDebug:
                print "goto step: %s" % current_step
        else:
            if IsDebug:
                print "form is not valid: %s" % current_step
                print form.errors

        return self.render(form, request, current_step)

    def render( self, form, request, step, context=None ):
        "Renders the given Form object, returning an HttpResponse."
        if IsDebug:
            print "make response"
        old_data = request.POST
        prev_fields = []
        if old_data:
            hidden = forms.HiddenInput()
            # Collect all data from previous steps and render it as HTML hidden fields.
            for i in range(step):
                old_form = self.get_form(i, old_data)
                prev_fields.extend([bf.as_hidden() for bf in old_form])
                hash_name = 'hash_%s' % i
                if IsDebug:
                    print hash_name
                prev_fields.append(hidden.render(hash_name, old_data.get(hash_name, self.security_hash(request, old_form))))
        return self.render_template(request, form, ''.join(prev_fields), step, context)

    def render_template( self, request, form, previous_fields, step, context=None ):
        """
        Renders the template for the given step, returning an HttpResponse object.

        Override this method if you want to add a custom context, return a
        different MIME type, etc. If you only need to override the template
        name, use get_template() instead.

        The template will be rendered with the following context:
            step_field -- The name of the hidden field containing the step.
            step0      -- The current step (zero-based).
            step       -- The current step (one-based).
            step_count -- The total number of steps.
            form       -- The Form instance for the current step (either empty
                          or with errors).
            wizardform -- The WizardForm instance for the current step including formsets.
            previous_fields -- A string representing every previous data field,
                          plus hashes for completed forms, all in the form of
                          hidden fields. Note that you'll need to run this
                          through the "safe" template filter, to prevent
                          auto-escaping, because it's raw HTML.
        """
        if IsDebug:
            print "render: %s" % step

        context = context or {}
        context.update(self.extra_context)
        context_instance = RequestContext(request)
        template = self.get_template(step)
        fieldsets = form.fieldsets
        
        data = request.POST.copy()
        data['step'] = step

        wizardForm = WizardForm( data, form, fieldsets )

        response = dict(context,
            step_field=STEP_FIELD_NAME,
            step0=step,
            step=step + 1,
            step_count=self.num_steps(),
            form=form,
            wizardform=wizardForm,
            previous_fields=previous_fields,
            media=self.media,
            )

        if form.cooked:
            for i, f, v, s in form.cooked:
                response[i] = request.POST.get(self.get_fieldname_for_step(s, f), None) or ''
                response['value_%s' % i] = request.POST.get(self.get_fieldname_for_step(s, v), None) or PK_EMPTY
        response['pk'] = form.instance.pk or PK_EMPTY

        if form.errors: # or step==2:
            errors = form.errors
            #raise 1

        if IsDebug:
            print "OK"
        return render_to_response(template, response, context_instance=context_instance)

    def _media( self ):
        js = ['js/foreignkey.updater.js', 'js/timer.widget.js', 'js/calendar.js', 'js/admin/DateTimeShortcuts.js']
        css = ['css/forms.css']
        return forms.Media(js=['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in js],
                           #css={'all': tuple(['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in css])}
                           )
    media = property(_media)


class WizardForm( object ):
    """
        Wizard Form prototype
    """
    def __init__( self, request, form, fieldsets ):
        self.request, self.form, self.fieldsets = request, form, fieldsets

    def __iter__( self ):
        for name, options in self.fieldsets:
            yield WizardFieldset( self.request, self.form, name, **options )

    def first_field( self ):
        try:
            fieldset_name, fieldset_options = self.fieldsets[0]
            field_name = fieldset_options['fields'][0]
            if not isinstance(field_name, basestring):
                field_name = field_name[0]
            return self.form[field_name]
        except (KeyError, IndexError):
            pass
        try:
            return iter(self.form).next()
        except StopIteration:
            return None

    def _media( self ):
        media = self.form.media
        for fs in self:
            media = media + fs.media
        return media
    media = property(_media)


class WizardFieldset( object ):
    """
        Wizard Fieldset prototype
    """
    def __init__( self, request, form, name, fields=(), classes=(), description=None, options=None ):
        self.request = request
        self.form = form
        self.name, self.fields = name, fields
        self.classes = u' '.join(classes)
        self.description = description
        self.layouts = options and options.get('layouts') or None

    def __iter__( self ):
        layouts_size = self.layouts and len(self.layouts) or 0
        for i, field in enumerate(self.fields):
            layout = self.layouts and i < layouts_size and self.layouts[i] or None
            yield WizardFieldline( self.request, self.form, field, layout )

    def _media( self ):
        if 'collapse' in self.classes:
            return forms.Media(js=['%sjs/admin/CollapsedFieldsets.js' % settings.ADMIN_MEDIA_PREFIX])
        return forms.Media()
    media = property(_media)


class WizardFieldline( object ):
    """
        Wizard Fieldline prototype
    """
    def __init__( self, request, form, field, layout=None ):
        self.request = request
        self.form = form
        if not isinstance(field, (list, tuple)):
            self.fields = [field]
        else:
            self.fields = field
        self.layout = layout in FORMLINES_LIST and layout or 'default'

    def __iter__( self ):
        for i, field in enumerate(self.fields):
            #print "%s" % field
            if self.layout == 'hidden':
                yield self.form[field].as_hidden()
            else:
                yield WizardField( self.request, self.form, field, is_first=(i == 0) )

    def errors( self ):
        return mark_safe(u'\n'.join([self.form[f].errors.as_ul() for f in self.fields if f != 'id']).strip('\n'))

    def line_as_default( self ):
        return self.layout == 'default' and 1 or 0

    def line_as_hidden( self ):
        return self.layout == 'hidden' and 1 or 0

    def line_as_table( self ):
        return self.layout == 'table' and 1 or 0

    def line_as_div( self ):
        return self.layout == 'div' and 1 or 0


class WizardField( object ):
    """
        Wizard Field prototype
    """
    def __init__( self, request, form, field, is_first ):
        if isinstance(field, dict) and 'id' in field.keys():
            # Get ForeignKey filter id-spec for corresponding table
            model = form._meta.model
            ids = field['id']
            value = None
            kw = {}
            if ids and isinstance(ids, (list, tuple)):
                for id in ids:
                    value = request.get(id[1]) or PK_EMPTY
                    if value is not None:
                        kw[id[0]] = value
                if kw:
                    choices = model.objects.filter(**kw) #.order_by('RD', 'title')
            if not kw:
                choices = model.objects.all() #.order_by('RD', 'title')

            #print "bound[%s:%s]" % (id, value)
            self.field = BoundField(form, ModelChoiceField(
                    choices[:int(getattr(settings, 'CHOICES_UPLOAD_LIMIT', 100))], 
                    required=False,
                    widget=AdvSelect(attrs={'class':'vLargeSelectField'}, 
                        extra_attrs={'onclick':'javascript:new_%s(%s);' % (_form_name(form), request.get('step', 0))}),
                    label='Select from the list',
                ), 'id')
        else:
            self.field = form[field]
        self.is_first = is_first
        self.is_checkbox = isinstance(self.field.field.widget, forms.CheckboxInput)

    def is_id( self ):
        return self.field.name == 'id' and True or False

    def label_tag( self ):
        classes = []
        if self.is_checkbox:
            classes.append(u'vCheckboxLabel')
            contents = force_unicode(escape(self.field.label))
        else:
            contents = force_unicode(escape(self.field.label)) + u':'
        if self.field.field.required:
            classes.append(u'required')
        if not self.is_first:
            classes.append(u'inline')
        attrs = classes and {'class': u' '.join(classes)} or {}
        return self.field.label_tag(contents=contents, attrs=attrs)

#
# ========================================================================================================
#

class CompanyWizardForm( CompanyForm ):
    """
        *Company* wizard form
    """
    cooked = None
    custom_validation = None

    fieldsets = [
        (_('Company'), {
                'fields'  : [
                   {'id'  : ()},
                    'country',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('div', 'table',)}
            }),
        (_('Title & Description'), {
                'fields'  : [
                    'title', 
                    'name',
                    'code',
                    'description',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('table', 'default', 'table', 'table',)}
            }),
    ]

    title = forms.CharField( required=True, initial='',
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    name = forms.CharField( required=False, initial='', label='Company Name',
            widget=forms.TextInput(attrs={'class':'vLargeTextField', 'style':'width:50%'}),
        )
    description = forms.CharField( required=False, initial='',
            widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':5}),
        )


class BranchWizardForm( BranchForm ):
    """
        *Branch* wizard form
    """
    cooked = [ ('company', 'title', 'pk', 0), ('pay', 'title', 'pk', 3), ('account', 'title', 'pk', 4), ]
    custom_validation = ('cooked',)

    fieldsets = [
        (_('Branch'), {
                'fields'  : [
                   {'id'  : (['company', '0-pk'],)},
                   #'company', 
                    'country', 
                    'type', 
                    'IsHeadOffice',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('div', 'table', 'table', 'table',)}
            }),
        (_('Title & Description'), {
                'fields'  : [
                    'title', 
                    'address',
                   ('city', 'postcode', ),
                   ('phone1', 'phone2',),
                    'fax',
                    'email',
                ], 
                'classes' : ['aligned'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table', 'table', 'table',)}
            }),
        (_('Notes & Misc'), {
                'fields' : [
                    'notes',
                   ('pay', 'account',),
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('table', 'hidden',)}
            }),
    ]

    title = forms.CharField( required=True, initial='',
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    address = forms.CharField( required=False, initial='',
            widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':2}),
        )
    email = forms.CharField( required=True, initial='', label='Email',
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    notes = forms.CharField( required=False, initial='',
            widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':5}),
        )
    country = forms.ModelChoiceField( Country.objects.all(), required=True )


class ContactWizardForm( ContactForm ):
    """
        *Contact* wizard form
    """
    cooked = [ ('company', 'title', 'pk', 0), ('branch', 'title', 'pk', 1), ]
    custom_validation = ('cooked',)

    fieldsets = [
        (_('Contact'), {
                'fields' : [
                   {'id'  : (['company', '0-pk'], )}, #['branch', '1-pk'],
                   #'company', 
                   #'branch', 
                    'salutation', 
                    'IsManager',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('div', 'table', 'table',)}
            }),
        (_('Title & Description'), {
                'fields'  : [
                    'title',
                    'name',
                   ('phone', 'mobile',),
                    'email',
                    'notes',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table', 'table',)}
            }),
    ]

    title = forms.CharField( required=True, initial='',
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    email = forms.CharField( required=True, initial='', label='E-mail',
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    notes = forms.CharField( required=False, initial='',
            widget=forms.Textarea(attrs={'class':'vLargeTextField', 'rows':5}),
        )


class PayStructureWizardForm( PayStructureForm ):
    """
        *Pay Structure* wizard form
    """
    cooked = [ ('company', 'title', 'pk', 0), ('branch', 'title', 'pk', 1), ('contact', 'title', 'pk', 2), ]
    custom_validation = ('cooked',)
    primary_reference = '1-pay'

    synonym = 'pay'

    fieldsets = [
        (_('PayStructure'), {
                'fields'  : [
                   {'id'  : ()},
                    'type',
                    'fixed_fee',
                    'amendments',
                ],
                'classes' : ['aligned', 'custom'],
                'options' : {'layouts' : ('div', 'div', 'table', 'table',)}
            }),
        (_('Title & Prices'), {
                'fields'  : [
                    'title', 
                   ('price1',  'max1',),
                   ('price2',  'max2',),
                   ('price3',  'max3',),
                   ('price4',  'max4',),
                   ('price5',  'max5',),
                   ('price6',  'max6',),
                   ('price7',  'max7',),
                   ('price8',  'max8',),
                   ('price9',  'max9',),
                   ('price10', 'max10',),
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table', 'table', 'table', 'table', 'table', 'table', 'table', 'table',)}
            }),
    ]

    title = forms.CharField( required=True, initial='',
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    type = forms.IntegerField( required=True, initial=0, label="Type of Price",
            widget=forms.RadioSelect(choices=PAY_CHOICES),
        )


class MYOBWizardForm( MYOBForm ):
    """
        *MYOB* wizard form
    """
    cooked = [ ('company', 'title', 'pk', 0), ('branch', 'title', 'pk', 1), ('contact', 'title', 'pk', 2), \
               ('pay', 'title', 'pk', 3), ]
    custom_validation = ('cooked',)
    primary_reference = '1-account'

    synonym = 'account'

    fieldsets = [
        (_('MYOB'), {
                'fields'  : [
                   {'id'  : ()},
                    'type',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('div', 'table',)}
            }),
        (_('Title & Details'), {
                'fields'  : [
                    'title', 
                   ('myobaccount', 'myobvat',),
                    'myobcompany',
                    'myobquantity',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table',)}
            }),
    ]

    title = forms.CharField( required=True, initial='',
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    type = forms.IntegerField( required=True, initial=0, label="Type",
            widget=forms.Select(choices=MYOB_CHOICES),
        )
    myobcompany = forms.CharField( required=False, initial='', label="MYOB Company Name",
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    myobquantity = forms.IntegerField( required=False, initial=1, label="Quantity", )


class JobWizardForm( JobForm ):
    cooked = [ ('company', 'title', 'pk', 0), ('branch', 'title', 'pk', 1), ('contact', 'title', 'pk', 2), \
               ('pay', 'title', 'pk', 3), ('account', 'title', 'pk', 4), ]
    custom_validation = ('cooked',)
    #exclude = ('amendments',)

    fieldsets = [
        (_('Job'), {
                'fields'  : [
                   {'id'  : (['company', '0-pk'], ['branch', '1-pk'], ['contact', '2-pk'],)},
                    'type',
                    'status', 
                ],
                'classes' : ['aligned', 'custom'],
                'options' : {'layouts' : ('div', 'div', 'table',)}
            }),
        (_('Title & Description'), {
                'fields'  : [
                    'title',
                    'code',
                    'user',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table',)}
            }),
        (_('Details'), {
                'fields'  : [
                   ('property', 'square',),
                   ('default', 'price',),
                    'calculated',
                   ('amend_total', 'amendments',),
                    'received', 
                    'runtime',
                    'finished',
                   #'IsAmendment',
                    'IsArchive',
                ],
                'classes' : ['aligned'],
                'options' : {'layouts' : ('table', 'table', 'table', 'table', 'default', 'table', 'default', 'table', 'table',)}
            }),
    ]

    title = forms.CharField( required=True, initial='', label="Property Address",
            widget=forms.TextInput(attrs={'class':'vLargeTextField'}),
        )
    type = forms.IntegerField( required=True, initial=0, label="Type",
            widget=forms.RadioSelect(choices=PRICE_CHOICES),
        )
    received = forms.SplitDateTimeField( required=True, 
        widget=AdminSplitDateTime(), 
    )
    # if field is required, set initial=None, else initial=0
    runtime = forms.IntegerField( required=True, label="Estimated run-time", initial=None,
        widget=CountDownTimer( days=1, extra_attrs={'style':'text-align:center;', 'maxlength':2} ),
    )
    finished = forms.SplitDateTimeField( required=False, 
        widget=AdminSplitDateTime(), 
    )

#
# ========================================================================================================
#

class ClientWizard( WizardModel ):
    """
        Client-entry Wizard
    """
    execution_sequence = (0, 3, 4, 1, 2, 5,)

    def __init__( self, form_list, initial=None ):
        super(WizardModel, self).__init__(form_list, initial)
        self.actions = {}

    def process_step( self, request, form, step ):
        #
        # Make action list for the current step (new records foreign keys resolving).
        #
        if IsDebug:
            print "process step: %s" % step
        if step == 0:
            self.actions = {}
        cooked = getattr(form, 'cooked', None)
        if not cooked:
            self.actions[step] = []
            return

        # Get actions stack
        actions = self.actions.get(step, None) or []

        # Check cooked items for the model,
        # if requested value is empty, new foreign key should be resolved:
        #    i -- foreign key id
        #    f -- unique model field id
        #    v -- requested item
        #    s -- from step
        for i, f, v, s in cooked:
            key = self.get_fieldname_for_step(step, i)
            value = request.POST.get(self.get_fieldname_for_step(s, v))
            # Check whether given field defined in the form model (exists in request)
            if form.fields.has_key(i): # and request.POST.has_key(key): # and request.POST.get(key) == PK_EMPTY:
                actions.append((i, f, v, s))

        # Updated action list for given step
        self.actions[step] = actions

    def done( self, request, current_step ):
        #
        # Perform final update
        #
        if IsDebug:
            print "done: %s" % repr(self.actions)
        # Data from request
        data = request.POST.copy()
        # Stack of previous forms
        pforms = []
        ids = {}

        # For every form
        for step in self.execution_sequence:
            if step > current_step:
                continue
            form = self.form_list[step]
            pk = data.get(self.get_fieldname_for_step(step, 'pk'))

            # Check actions list
            actions = self.actions.get(step) or []
            IsAdd = IsChanged = 0

            # If reqistered
            for i, f, v, s in actions:
                key = self.get_fieldname_for_step(step, i)
                value = ids.get(i, None) # or data.get(self.get_fieldname_for_step(s, v), None)
                if value is None:
                    continue
                #if data.get(key, None) != PK_EMPTY: # not data.has_key(key) or
                #    continue
                """
                # Get a form
                if s >= len(pforms):
                    continue
                # Get corresponding model
                model = pforms[s]._meta.model
                # Run query, where select records matched with table unique value
                kw = { f: data.get(self.get_fieldname_for_step(s, f)) }
                rows = model.objects.filter(**kw)
                # If record(s) exists
                if rows:
                    # Update requested field with new record 'id' value
                    data[key] = rows[0].id
                """
                data[key] = ids.get(i)
                if IsDebug:
                    print "%s add: id=%s, key=%s, step=%s, value=%s" % (step, i, key, s, data[key])

            # Refresh a form with new data
            new_form = self.get_form(step, data)

            # Check changed fields
            if pk == PK_EMPTY:
                IsAdd = 1
                form._changed_data = None
            else:
                IsChanged = 1
                form._changed_data = []
                for key in new_form.fields.keys():
                    if key in ('RD',):
                        continue
                    if key in DATE_FIELDS:
                        new = data.get(self.get_fieldname_for_step(step, key+'_0'), '') + ' ' + \
                              data.get(self.get_fieldname_for_step(step, key+'_1'), '')
                        new = new.strip()
                    elif key in BOOLEAN_FIELDS:
                        new = data.get(self.get_fieldname_for_step(step, key), None)
                        if new is None or new in ('', 'False', '0', 'off', 'None'):
                            new = '0'
                        else:
                            new = '1'
                    else:
                        new = data.get(self.get_fieldname_for_step(step, key), '')
                    if not isinstance(new, basestring):
                        new = str(new)
                    old = getattr(new_form.instance, key, None)
                    if isinstance(old, models.Model):
                        old = str(old.id)
                    if old is None:
                        old = ''
                    elif not isinstance(old, basestring):
                        old = str(old)
                    if new != old:
                        form._changed_data.append('%s(OLD[%s] - NEW[%s])' % (key, old, new))
                IsAdd = 0

            # Check and save
            model_name = getattr(form, 'synonym', None) or _form_name(form)
            if not IsAdd and not form._changed_data:
                ids[model_name] = pk
                IsChanged = 0
            if new_form.is_valid():
                #print 'is valid'
                if IsAdd or IsChanged:
                    new_item = new_form.save() # commit=False
                    ids[model_name] = new_item.id
                    message = construct_change_message(form, 'DataEntry Wizard')
                    if IsAdd:
                        log_addition(request, new_item, message)
                    else:
                        log_change(request, new_item, message)
            else:
                # Validate all the forms. If any of them fail validation, that
                # must mean the validator relied on some other input, such as
                # an external Web site.
                return self.render_revalidation_failure(request, step, new_form)
            # Add previous form to stack
            pforms.append( new_form )

        return render_to_response('thanks.html', {
            'form_data': [ form.cleaned_data for form in pforms ],
            'title': 'Committed successfully',
        })
    done = transaction.commit_on_success(done)

    def get_template( self, step ):
        #if step == 2: raise 1
        return ['jobs/wizard_%s.html' % step, 'forms/wizard.html']
