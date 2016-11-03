// ******************************
// COMMON DECLARATIONS /common.js
// ------------------------------
// Version: 2.0
// Date: 16-10-2016

// -------------
// Clock routine
// -------------

var TID, seconds, back_seconds, s, l, server_requests_count = 0;
var SPLITTER = '_';

function _r(x) {
    s = '00' + x.toString();
    l = s.length;
    return s.substring(l-2, l);
}

function update_seconds() {
    s = '00' + seconds.toString();
    l = s.length;
    $("#_sec").html(s.substr(l-2, 2));
    TID = window.setTimeout("interrupt(1)", 1000);
}

function interrupt(mode) {
    back_seconds += -1;
    seconds += 1;

    if (back_seconds <= 0) {
        get_server_time();
    } else {
        update_seconds();
    }
}

function repeat_it() {
    if (server_requests_count == 3) {
        var clock = document.getElementById('clock');
        clock.innerHTML = '';
    } else {
        get_server_time();
    }
}

function get_server_time() {
    var ds = new Date();
    server_requests_count += 1;
    $.get("loader", {'mode':'time'}, function(x) {
        var items = x.split('#');
        var df = new Date();
        var n = new Number(df-ds);

        seconds = parseInt(items[2]);
        if (isNaN(seconds) || seconds >= 60 || seconds < 0) {
            return repeat_it();
            
        }
        if (seconds < 59) {
            seconds = n > 50 ? seconds + (n > 1000 ? (n/1000).toFixed() + 1 : 0) : seconds;
            if (seconds > 59) {
                return repeat_it();
            }
        }
        back_seconds = 60 - seconds;
        server_requests_count = 0;

        $("#_date").html(items[0]);
        $("#_time").html(items[1]);

        update_seconds();
    });
}

function startClock() {
    var clock = document.getElementById('clock'); //$("#clock");
    if (clock != null && typeof(clock) == 'object') {
        var x = '<div class="datetime"><span id="_date">0000-00-00</span>&nbsp;<span id="_time">00:00</span>:<span id="_sec">00</span></div>';
        clock.innerHTML = x; //clock.html(x);
        get_server_time();
    }
}

function $_init() {
    $("#index-container").removeClass('hidden');
    
    startClock();
}

// ----------------------
// Dialog Action Handlers
// ----------------------

function $ToggleBox(ob, key, action, e) {
    var id = ob.attr('id').split(SPLITTER)[1];
    var oid = key+id;
    var child = $("#"+oid);
    var class_hidden = 'hidden';

    //alert(id+'...'+oid+'...'+child.attr('id'));

    switch (action)
    {
        case 'show':
            if (child.hasClass(class_hidden))
                child.removeClass(class_hidden);
            break;
        case 'hide':
            if (!child.hasClass(class_hidden))
                child.addClass(class_hidden);
            break;
        default:
            child.toggleClass(class_hidden);
    }    

    if (e != null) {
        e.stopPropagation();
        e.preventDefault();
    }
}

// ====================
// Page Event Listeners
// ====================

$(document).ready(function() {
    $("*", document.body).click(function (e) {
        var ob = $(this);
        var id = ob.attr('id');
        //
        //  Show/Hide filter panel
        //
        if (id == 'show-filter') {
            $("#filter-panel").show();
            $("#filter-show").attr('value', '1');
            //$("#changelist-search").submit();
        }
        if (id == 'hide-filter') {
            $("#filter-panel").hide();
            $("#filter-show").attr('value', '0');
            //$("#changelist-search").submit();
        }
        //
        // Open an item
        //
        if (ob.hasClass('lookup')) {
            e.stopPropagation();
            return true;
        }

        var parent = ob.parent();
        if (parent.hasClass('item-list')) {
            var href = $("th", parent).find("a").attr("href");
            window.location = href;
            e.stopPropagation();
            return false;
        }

        if (ob.hasClass('rlink')) e.stopPropagation();
    });

    // For round page header corners should be included in base.html:
    // <script type="text/javascript" src="/media/js/jquery.corner.js"></script>
    // Uncomment the line:
    //$("#content-title").corner("round tr bl 15px");
});

// =======
// STARTER
// =======

/* window.onload = function() { startClock(); } */

$(function() 
{
    $_init();
});
