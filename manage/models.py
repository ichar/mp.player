#######################################################################################
# MakingPlans Job Details Database.
# ---------------------------------
# Django LogEntry class model ovveridence.
#
# Checked: 2011/11/07
# ichar@g2.ru
#
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.admin.util import quote
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe

ADDITION = 1
CHANGE = 2
DELETION = 3

class LogEntryManager( models.Manager ):
    def log_action(self, user_id, content_type_id, object_id, object_repr, action_flag, change_message=''):
        e = self.model(None, None, user_id, content_type_id, smart_unicode(object_id), object_repr[:200], action_flag, change_message)
        e.save()

class LogEntry( models.Model ):
    action_time = models.DateTimeField(_('action time'), auto_now=True)
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.TextField(_('object id'), blank=True, null=True)
    object_repr = models.CharField(_('object repr'), max_length=200)
    action_flag = models.PositiveSmallIntegerField(_('action flag'))
    change_message = models.TextField(_('change message'), blank=True)
    objects = LogEntryManager()

    class Meta:
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        db_table = 'django_admin_log'
        ordering = ('-action_time',)

    def __repr__( self ):
        return smart_unicode(self.action_time)

    def caption( self ):
        return """<a href=\"../../../%s\" class=\"lookup\" id=\"lookup_id_%s\">%s</a>""" % \
            ( self.get_admin_url(), self.object_id, self.object_repr )
    caption.allow_tags = True
    caption.short_description = _('Caption')
    caption.admin_order_field = 'object_repr'

    def object_short_repr( self ):
        sep = '...'
        l = 24
        s = ' '.join([len(x) > l and ('%s%s' % (x[:l], sep)) or x for x in self.object_repr.split(' ')])
        if sep in s:
            return s[:s.find(sep)+len(sep)]
        return s

    def is_addition( self ):
        return self.action_flag == ADDITION

    def is_change( self ):
        return self.action_flag == CHANGE

    def is_deletion( self ):
        return self.action_flag == DELETION

    def get_edited_object(self):
        "Returns the edited object represented by this log entry"
        return self.content_type.get_object_for_this_type(pk=self.object_id)

    def get_admin_url( self ):
        """
        Returns the admin URL to edit the object represented by this log entry.
        This is relative to the Django admin index page.
        """
        return mark_safe(u"%s/%s/%s/" % (self.content_type.app_label, self.content_type.model, quote(self.object_id)))

    def rendered_user( self ):
        html = """<nobr><span id=\"user_%s_%s\" name=\"old_user\" class=\"custom_user\">%s</span></nobr>"""
        if self.user is not None:
            return html % ( self.user, self.user.id, self.user )
        return html % ( self.user, '0', '---' )
    rendered_user.allow_tags = True
    rendered_user.short_description = _('User')
    rendered_user.admin_order_field = 'user'

    def rendered_action( self ):
        media_url = '/media/img'
        if self.is_addition():
            return '<img src="%s/perm_add.png" title="add" alt="add">' % media_url
        elif self.is_change():
            return '<img src="%s/perm_change.png" title="change" alt="change">' % media_url
        elif self.is_deletion():
            return '<img src="%s/perm_delete.png" title="delete" alt="delete">' % media_url
    rendered_action.allow_tags = True
    rendered_action.short_description = _('Action')
    rendered_action.admin_order_field = 'action_flag'

    def rendered_action_time( self ):
        html = """<nobr><b>%s</b>&nbsp;(<span class="rendered_time">&nbsp;%s&nbsp;</span>)</nobr> :&nbsp;<span class="rendered_dayofweek">%s</span>"""
        D = self.action_time.strftime('%d %b %Y')
        T = self.action_time.strftime('%H:%M:%S')
        w = self.action_time.strftime('%a')
        return html % (D, T, w)
    rendered_action_time.allow_tags = True
    rendered_action_time.short_description = _('Action time')
    rendered_action_time.admin_order_field = 'action_time'

    def rendered_content_type( self ):
        return '<nobr><div class="rendered_type">%s</div></nobr>' % self.content_type
    rendered_content_type.allow_tags = True
    rendered_content_type.short_description = _('Content type')
    rendered_content_type.admin_order_field = 'content_type'

    def rendered_object_id( self ):
        if self.object_id is None or self.object_id == 'None':
            return '---'
        return self.object_id
    rendered_object_id.allow_tags = False
    rendered_object_id.short_description = _('OID')
    rendered_object_id.admin_order_field = 'object_id'

    def rendered_message( self ):
        s = self.change_message or ''
        if 'FlowLogic' in s or 'DataEntry' in s:
            i = s.find(':')
            caption = s[:i]
            s = '<br>\n'.join([unichr(0x25a0)+'&nbsp;'+x for x in s[i+1:].split(',')])
            return '%s:<br>%s' % (caption, s)
        else:
            return s
    rendered_message.allow_tags = True
    rendered_message.short_description = _('Description')
    rendered_message.admin_order_field = 'change_message'
