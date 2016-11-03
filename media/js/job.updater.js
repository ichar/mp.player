// *****************************
// JOBS HANDLERS /job.updater.js
// -----------------------------
// Version: 2.1
// Date: 28-10-2016

// ------------------
// Grid functionality
// ------------------

var IsStatusShown = null;
var StatusOver = 0;
var IsUserShown = null;
var UserOver = 0;
var IsMailShown = null;
var MailOver = 0;

var mail_prefix = 'mail-';

var OVER_COUNT    = 10;
var STATUS_OFFSET = 12;
var USER_OFFSET   = 12;
var MAIL_OFFSET   = 12;
var H_INC         = 5;
var V_INC         = 0;

function confirmMail(status) {
    if( IsMailShown && status > -1 ) {
        var x = IsMailShown.split('|');
        var oid = x[0];
        var id = oid.split('-')[1];
        var row_id = id.split('_');
        var href = x[1];
        var ob = $("#"+id);

        window.location.href = href;
        if( typeof(ob) == 'object' && status > 0 ) changeStatus(id, status, 'mail');
    }
}

function changeStatus(id, status, message) {
    var row_id = id.split('_');
    var mail_id = mail_prefix+'status_'+row_id[1]+'_'+row_id[2];
    var author = $("#author").val();

    if( id && status ) {
        var ob = $("#"+id);
        var new_id = 'status_' + row_id[1] + '_' + status.toString();

        $.get("loader", {'mode':'check_status', 'id':id, 'value':status}, function(IsChanged) {
            if( !IsChanged || confirm('Status of the given job has been change before by another user.\nDo you really wish to change it anyway?\n\nPlease, confirm.') ) {
                $.getJSON("loader", {'mode':'change_status', 'id':id, 'value':status, 'author':author, 'message':message}, function(x) {
                    $.each(x, function(i, item) {
                        ob.removeClass(ob.text().toLowerCase()).addClass(item.fields.title.toLowerCase());
                        ob.text(item.fields.title);
                        ob.attr('id', new_id);
                        $("#"+mail_id).attr('id', mail_prefix + new_id);
                    });
                });
            } else $("#changelist-search").submit();
        });
    }
}

function saveAmendments(id, e) {
    var author = $("#author").val();
    $.get("loader", {'mode':'AMD', 'id':id, 'author':author}, function(x) {
        var oid = id.split('_')[1];
        var src = '/media/img/admin/icon-';
        if (x) {
            $("#"+id).html(x);
            src += 'yes.gif';
        } else {
            src += 'no.gif';
        }
        $("#AC_"+oid).attr('src', src);
    });
    e.stopPropagation();
}

function _get_notes_tracker(id) {
    return $("#tracker"+SPLITTER+id);
}

function _get_notes_container(id) {
    return $("#notesbox"+SPLITTER+id);
}

function saveNotes(id) {
    var author = $("#author").val();
    var ob = $("#notesarea"+SPLITTER+id);
    var value = ob.val();

    $.post("tracker", {'mode':'notes', 'id':id, 'author':author, 'value':value}, function(x) {
        refreshNotes(id, x);
    });
}

function hideNotes(id, value) {
    var tracker = _get_notes_tracker(id);
    $ToggleBox(tracker, 'notes_', 'hide', null);
}

function refreshNotes(id, value) {
    var container = _get_notes_container(id);

    if (container == null) 
        return;

    container.html('');
    container.append(value);
    container.attr('mode', 'hidden');

    var tracker = _get_notes_tracker(id);

    if (tracker == null) 
        return;

    if (value.length > 0) {
        if (tracker.children("img").length > 0) 
            return;

        tracker.append((
                '<img class="notes" src="/media/img/admin/notes-1.png" alt="Notes" id="nic:ID">'
            )
            .replace(/ID/g, id)
        );
    } else {
        var title = tracker.children("div").html();
        tracker.html('<div class="title">'+title+'</div>');
    }

    $ToggleBox(tracker, 'notes_', 'hide', null);
}

function openNotesTracker(ob, e) {
    var id = ob.attr('id').split(SPLITTER)[1];
    var container = _get_notes_container(id);

    if (container == null) 
        return;

    var value = container.html()
        .replace(/<p>|<\/p>/g, '')
        .replace(/<br>/g, '\n')
        ;

    var mode = container.attr('mode');

    if (mode != 'shown') {
        container.html('');

        container.append((
                '<h3>Change Job Notes:</h3>'+
                '<div class="notescontainer">'+
                '<textarea class="notesbox" id="notesarea_ID">VALUE</textarea>'+
                '<div class="simplepanel">'+
                    '<button id="ok" class="btn indented" onclick="javascript:saveNotes(ID);">'+'Save'+'</button>'+
                    '<button id="cancel" class="btn" onclick="javascript:hideNotes(ID);">'+'Close'+'</button>'+
                '</div></div>'
            )
            .replace(/ID/g, id)
            .replace(/VALUE/g, value)
        );

        container.attr('mode', 'shown');
    }

    $ToggleBox(ob, 'notes_', 'show', e);
}

// ====================
// Page Event Listeners
// ====================

$(document).ready(function() {
    $("*", document.body).click(function (e) {
        var ob = $(this);
        var id = ob.attr('id');
        //
        // Open Notes tracker
        //
        if (ob.hasClass('tracker')) {
            openNotesTracker(ob, e);
            return false;
        }
        //
        //  Amendments Count updater
        //
        if (ob.hasClass("AMD")) {
            saveAmendments(id, e);
            return;
        }
        //
        //  Hide changes boxes
        //
        if( !IsStatusShown && !IsUserShown && !IsMailShown ) return;

        e.stopPropagation();

        var status = $("#new_status_container");
        if( typeof(status) != 'object' )
            return;

        if( !id || id.indexOf('status') != 0 ) {
            status.hide();
            IsStatusShown = null;
            StatusOver = 0;
        }

        if( !IsUserShown && !IsMailShown ) return;

        var user = $("#new_user_container");
        if( typeof(user) != 'object' )
            return;

        if( !id || id.indexOf('user') != 0 ) {
            user.hide();
            IsUserShown = null;
            UserOver = 0;
        }

        if( !IsMailShown ) return;

        var mail = $("#new_mail_container");
        if( typeof(mail) != 'object' )
            return;

        if( !id || id.indexOf('mail') != 0 ) {
            mail.offset({top:-1000, left:-1000});
            mail.hide();
            IsMailShown = null;
            MailOver = 0;
        }
    });
    //
    //  Status changes box
    //
    $("input[name='new_status']").change(function (e) {
        var ob = $(this);

        //alert('new_status:'+IsStatusShown+':'+ob.attr('checked'));

        if( IsStatusShown && ob.attr('checked') ) {
            changeStatus(IsStatusShown, ob.attr('value'), 'new status');
        }

        e.stopPropagation();

        var status = $("#new_status_container");
        if( typeof(status) == 'object' ) {
            IsStatusShown = null;
            status.hide();
        }

        StatusOver = 0;
    });

    $("span[name='old_status']").mousemove(function (e) {
        if( StatusOver <= OVER_COUNT ) {
            StatusOver += 1;
            return;
        }
        var ob = $(this);
        var checked_status = ob.attr('id').split('_')[2];
        var offset = ob.offset();
        var container = $("#new_status_container");
        var x = offset.top - container.height() - STATUS_OFFSET - V_INC;
        if( x < 0 ) x = 0;
        x = Math.round(x);
        var y = offset.left + ob.width() + STATUS_OFFSET + H_INC;
        if( y > screen.width ) y = screen.width - container.width();
        y = Math.round(y);

        e.stopPropagation();

        if( typeof(container) == 'object' ) {
            container.offset({top:x, left:y});
            $("#status_id_"+checked_status).attr('checked', 'checked');
            container.show();
        }

        IsStatusShown = ob.attr('id');
    });
    //
    //  User changes box
    //
    $("input[name='new_user']").change(function (e) {
        var ob = $(this);
        var value = ob.attr('value');
        var id = IsUserShown;
        var row_id = id.split('_');
        var author = $("#author").val();
        
        if( ob.attr('checked') && id && value ) $.getJSON("loader", {'mode':'change_user', 'id':id, 'value':value, 'author':author}, function(x) {
            $.each(x, function(i,item) {
                $("#"+id).text(item.fields.username);
                $("#"+id).attr('id', 'user_'+row_id[1]+'_'+item.pk.toString());
            });
        });

        e.stopPropagation();

        var user = $("#new_user_container");
        if( typeof(user) == 'object' ) {
            IsUserShown = null;
            user.hide();
        }

        UserOver = 0;
    });

    $("span[name='old_user']").mousemove(function (e) {
        if( UserOver <= OVER_COUNT ) {
            UserOver += 1;
            return;
        }
        var ob = $(this);
        var checked_user = ob.attr('id').split('_')[2];
        var offset = ob.offset();
        var container = $("#new_user_container");
        var x = offset.top - container.height() - USER_OFFSET - V_INC;
        if( x < 0 ) x = 0;
        x = Math.round(x);
        //var y = offset.left - container.width() - USER_OFFSET - H_INC - 5;
        var y = offset.left + ob.width() + USER_OFFSET + H_INC;
        if( y > screen.width ) y = screen.width - container.width();
        y = Math.round(y);

        e.stopPropagation();

        if( typeof(container) == 'object' ) {
            container.offset({top:x, left:y});
            $("input[name='new_user']:checked", container).removeAttr('checked');
            if( parseInt(checked_user) )
                $("#user_id_"+checked_user).attr('checked', 'checked');
            container.show();
        }

        IsUserShown = ob.attr('id');
    });
    //
    //  Mail changes box
    //
    $("a[name='mail_job']").click(function (e) {
        var ob = $(this);
        var parent = ob.parent();
        var offset = parent.offset();
        var container = $("#new_mail_container");
        var x = offset.top - container.height() - MAIL_OFFSET - V_INC - 80;
        if( x < 0 ) x = 0;
        x = Math.round(x);
        var y = offset.left + parent.width() + MAIL_OFFSET + H_INC + 12;
        if( y > screen.width ) y = screen.width - container.width();
        y = Math.round(y);

        $("#mail_address").html(ob.html());

        e.stopPropagation();

        if( typeof(container) == 'object' ) {
            container.css('top', x).css('left', y);
            container.show();
        }

        IsMailShown = ob.attr('id')+'|'+ob.attr('href');
    });
    //
    //  Notes box
    //
    $("img[id^='nic']").click(function (e) {
        $ToggleBox($(this), "notes_", null, e);
    });
});
