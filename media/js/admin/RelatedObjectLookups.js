//
// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.
//

var subforms = {
    '/default/'      : 'top=70,left=50,width=800,height=400',
    '/company/'      : 'top=70,left=50,width=1100,height=580',
    '/branch/'       : 'top=70,left=50,width=920,height=600',
    '/contact/'      : 'top=70,left=50,width=860,height=590',
    '/job/'          : 'top=70,left=50,width=800,height=460',
    '/country/'      : 'top=70,left=50,width=800,height=360',
    '/department/'   : 'top=70,left=50,width=840,height=360',
    '/myob/'         : 'top=70,left=50,width=820,height=540',
    '/paystructure/' : 'top=70,left=50,width=860,height=660',
    '/status/'       : 'top=70,left=50,width=820,height=460',
    '/user/add/'     : 'top=70,left=50,width=800,height=440',
    '/user/'         : 'top=70,left=50,width=1200,height=620'
}

function get_window_attrs(url) {
    var s = 'directories=no,copyhistory=no,';
    for (var key in subforms)
        if (url.indexOf(key) != -1)
            return s + subforms[key];
    return s + subform['default'];
}

function html_unescape(text) {
    // Unescape a string that was escaped using django.utils.html.escape.
    text = text.replace(/&lt;/g, '<');
    text = text.replace(/&gt;/g, '>');
    text = text.replace(/&quot;/g, '"');
    text = text.replace(/&#39;/g, "'");
    text = text.replace(/&amp;/g, '&');
    return text;
}

// IE doesn't accept periods or dashes in the window name, but the element IDs
// we use to generate popup window names may contain them, therefore we map them
// to allowed characters in a reversible way so that we can locate the correct 
// element when the popup window is dismissed.

function id_to_windowname(text) {
    text = text.replace(/\./g, '__dot__');
    text = text.replace(/\-/g, '__dash__');
    return text;
}

function windowname_to_id(text) {
    text = text.replace(/__dot__/g, '.');
    text = text.replace(/__dash__/g, '-');
    return text;
}

function showRelatedObjectLookupPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^lookup_/, '');
    name = id_to_windowname(name);
    var href = triggeringLink.href;
    if (href.search(/\?/) >= 0) {
        href += '&_popup=1';
    } else {
        href += '?_popup=1';
    }
    var attrs = get_window_attrs(href)+',resizable=yes,scrollbars=yes';

    //alert(attrs);

    var win = window.open(href, name, attrs);
    win.focus();
    return false;
}

function dismissRelatedLookupPopup(win, chosenId) {
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
        elem.value += ',' + chosenId;
    } else {
        document.getElementById(name).value = chosenId;
    }
    win.close();
}

function showOpenPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^open_/, '');
    name = id_to_windowname(name);
    var href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=1';
    } else {
        href += '&_popup=1';
    }
    var attrs = get_window_attrs(href)+',resizable=yes,scrollbars=yes';
    var win = window.open(href, name, attrs);
    win.focus();
    return false;
}

function showAddAnotherPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^add_/, '');
    name = id_to_windowname(name);
    var href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=1';
    } else {
        href += '&_popup=1';
    }
    var attrs = get_window_attrs(href)+',resizable=yes,scrollbars=yes';
    var win = window.open(href, name, attrs);
    win.focus();
    return false;
}

function dismissAddAnotherPopup(win, newId, newRepr) {
    // newId and newRepr are expected to have previously been escaped by
    // django.utils.html.escape.
    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    if (elem) {
        if (elem.nodeName == 'SELECT') {
            var o = new Option(newRepr, newId);
            elem.options[elem.options.length] = o;
            o.selected = true;
        } else if (elem.nodeName == 'INPUT') {
            elem.value = newId;
        }
    } else {
        var toId = name + "_to";
        elem = document.getElementById(toId);
        var o = new Option(newRepr, newId);
        SelectBox.add_to_cache(toId, o);
        SelectBox.redisplay(toId);
    }
    win.close();
}