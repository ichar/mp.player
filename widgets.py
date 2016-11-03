#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# widgets.py
#
# Checked: 2010/05/16
# ichar@g2.ru
#
import re
import copy
import datetime
import settings
from itertools import chain

from django.forms.widgets import Widget, Select, SelectMultiple, CheckboxInput
from django.utils.dates import MONTHS
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.forms.util import flatatt

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')

class CheckboxList( SelectMultiple ):
    """
    Extra class for Select widget. Adds new item button.
    """
    def __init__( self, attrs=None, choices=(), extra_attrs=None ):
        super(CheckboxList, self).__init__(attrs)
        #
        # Choices can be any iterable, but we may need to render this widget
        # multiple times. Thus, collapse it into a list so it can be consumed
        # more than once.
        #
        self.choices = list(choices)
        self.extra_attrs = extra_attrs

    def render( self, name, value, attrs=None, choices=() ):
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<table class="checkboxlist" border="0">']

        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = CheckboxInput(final_attrs, 
                check_test=lambda value=value, checked=self.extra_attrs.get('checked'): checked or value in str_values
            )
    
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<tr><td>%s</td><td><label%s>%s</label></td></tr>' % (rendered_cb, label_for, option_label))

        output.append(u'</table>')
        return mark_safe(u'\n'.join(output))

    def id_for_label( self, id_ ):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_0'
        return id_
    id_for_label = classmethod(id_for_label)

class SelectMonthWidget( Widget ):
    """
    A Widget that splits date input into two <select> boxes.
    """
    month_field = '%s_month'
    year_field = '%s_year'

    def __init__( self, attrs=None, years=None ):
        # years is an optional list/tuple of years to use in the "year" select box.
        self.attrs = attrs or {}
        if years:
            self.years = years
        else:
            this_year = datetime.date.today().year
            self.years = range(this_year, this_year+10)

    def render( self, name, value=None, attrs=None ):
        try:
            year_val, month_val = value.year, value.month
        except AttributeError:
            year_val = month_val = None
            if isinstance(value, basestring):
                match = RE_DATE.match(value)
                if match:
                    year_val, month_val = [int(v) for v in match.groups()]

        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        month_choices = MONTHS.items()
        month_choices.sort()
        month_choices.insert(0, (0, '---'))
        local_attrs = self.build_attrs(id=self.month_field % id_)
        select_html = Select(choices=month_choices).render(self.month_field % name, month_val, local_attrs)
        output.append(select_html)

        year_choices = [(i, i) for i in self.years]
        local_attrs['id'] = self.year_field % id_
        select_html = Select(choices=year_choices).render(self.year_field % name, year_val, local_attrs)
        output.append(select_html)

        return mark_safe(u'\n'.join(output))

    def id_for_label( self, id_ ):
        return '%s_month' % id_
    id_for_label = classmethod(id_for_label)

    def value_from_datadict( self, data, files, name ):
        y, m = data.get(self.year_field % name), data.get(self.month_field % name)
        if y and m:
            return '%s-%s' % (y, m,)
        return data.get(name, None)

class AdvSelect( Select ):
    """
    Extra class for Select widget. Adds new item button.
    """
    def __init__( self, attrs=None, choices=(), extra_attrs=None ):
        super(AdvSelect, self).__init__(attrs)
        #
        # Choices can be any iterable, but we may need to render this widget
        # multiple times. Thus, collapse it into a list so it can be consumed
        # more than once.
        #
        self.choices = list(choices)
        self.extra_attrs = extra_attrs

    def render( self, name, value, attrs=None, choices=() ):
        if value is None:
            value = ''
        if self.extra_attrs and self.extra_attrs.has_key('onclick'):
            onclick = self.extra_attrs.get('onclick') and ' onclick="%s"' % self.extra_attrs['onclick'] or ''
        else:
            onclick = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append('</select><a class="addselectitem"%s><span>new</span></a>' % onclick)
        return mark_safe(u'\n'.join(output))

class CountDownTimer( Widget ):
    """
    Class realized "Count Down Timer" input.
    """
    attrs_default = {'size':2, 'width':'40px', 'style':'text-align:center;'}
    input_type = 'text'

    def __init__( self, interval=None, mins=1, hours=1, days=1, attrs=None, extra_attrs=None ):
        super(CountDownTimer, self).__init__(attrs)
        #
        # Timer will check minutes defined as *interval* value.
        # We can render minutes, hours and days.
        #
        try:
            self.interval = interval and int(interval) or 20
            self.is_mins = mins and 1 or not ( hours or days ) and 1 or 0
            self.is_hours = hours or 0
            self.is_days = days or 0
        except:
            self.interval = 20
            self.is_mins = self.is_hours = self.is_days = 1
        self.extra_attrs = self._check_default_attrs( extra_attrs )

    def _check_default_attrs( self, attrs ):
        for key in self.attrs_default.keys():
            if not attrs.has_key(key):
                attrs[key] = self.attrs_default[key]
        return attrs or {}

    def render( self, name, value, attrs=None ):
        #
        # Value is a list(tuple): [ int, datetime ] -- timer value, started from the date.
        # We should check how much time left before there is no time.
        #
        #print value
        if value is None:
            timer_value = 0
            started = None
            is_required = False
        else:
            timer_value = value
            started = None # XXX
            is_required = True
        v_days = v_hours = v_mins = 0
        if timer_value:
            try:
                v_days = int(timer_value / 1440) or 0
                v_hours = int(timer_value / 60) or 0
                v_mins = timer_value - (v_days * 1440 + v_hours * 60)
            except:
                pass

        # Tag attributes
        a = self.extra_attrs.copy()
        a.update(attrs)

        # Timer rendered values
        if self.is_mins:
            n = '%s_mins' % name
            a['id'] = 'id_%s' % n
            mins_attrs = self.build_attrs(a, type=self.input_type, name=n)
            mins_attrs['value'] = force_unicode(v_mins)
        if self.is_hours:
            n = '%s_hours' % name
            a['id'] = 'id_%s' % n
            hours_attrs = self.build_attrs(a, type=self.input_type, name=n)
            hours_attrs['value'] = force_unicode(v_hours)
        if self.is_days:
            n = '%s_days' % name
            a['id'] = 'id_%s' % n
            days_attrs = self.build_attrs(a, type=self.input_type, name=n)
            days_attrs['value'] = force_unicode(v_days)

        # Input tags
        output = ['<div class="timer" id="%s_timer"><table><tr>' % name]
        if self.is_days:
            output.append('<td><input%s disabled></td><td>&nbsp;Days&nbsp;</td>' % flatatt(days_attrs))
        if self.is_hours:
            output.append('<td><input%s disabled></td><td>&nbsp;Hours&nbsp;</td>' % flatatt(hours_attrs))
        if self.is_mins:
            output.append('<td><input%s disabled></td><td>&nbsp;Mins&nbsp;</td>' % flatatt(mins_attrs))
        output.append('</tr></table></div>')

        # Control buttons
        x = { 'media':settings.ADMIN_MEDIA_PREFIX, 'name': ("'%s'" % name), 'interval':self.interval }
        output.append('<div class="timer_buttons">')
        output.append("<img class=\"timer_up\" onclick=\"javascript:EvalTimer('up', %(name)s, %(interval)s);\""
                      " src=\"%(media)simg/admin/arrow-up.gif\"><br>" % x)
        output.append("<img class=\"timer_down\" onclick=\"javascript:EvalTimer('down', %(name)s, %(interval)s);\""
                      " src=\"%(media)simg/admin/arrow-down.gif\">" % x)
        output.append('</div>')
        if is_required:
            v = timer_value
        else:
            v = ''
        output.append('<input type="hidden" id="id_%s" name="%s" value="%s">' % (name, name, v))
        del x

        return mark_safe(u'\n'.join(output))
