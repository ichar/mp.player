$(window).unload(function() {
    var frm = document.forms[0];
    enableForm( frm );
});

var active_item = null;
var client_active_row = '';
var job_active_row = '';

var is_client_main_shown = 0;
var is_job_main_shown = 0;
var is_job_item_activated = 0;
var is_job_item_shown = 0;

var SELECTED_ROW_CLASS = 'flow-selected';

function onItem(id, mode) { 
    active_item = id;
    $("#active_item").attr('value', active_item);
    return false; 
}

function get_active_rows() {
    var x = $("#client_active_row").val();
    if( x && x != client_active_row ) client_active_row = x;
    var y = $("#job_active_row").val();
    if( y && y != job_active_row ) job_active_row = y;
}

function get_job_args(page) {
    var value = $("#flow-job-search-input").val();
    var args = {'q':value, 'p':page};
    if( client_active_row ) args['branch__exact'] = client_active_row.split('-')[3];
    var status = parseInt($("#id_status").val());
    if( status > -1 ) args['status__id__exact'] = status;
    var type = parseInt($("#id_type").val());
    if( type > -1 ) args['type__exact'] = type;
    return args
}
//
// Show/Hide Flow frames
//
function showClientFrames() {
    $("#flow-client-results").show();
    $("#flow-client-search-hide").attr('disabled', false);
    $("#flow-client-search-show").attr('disabled', false);
    var row = $("tr[name='flow-row-client']:first");
    row.addClass(SELECTED_ROW_CLASS);
    client_active_row = row.attr('id');
    $("#client_active_row").attr('value', client_active_row);
}

function hideClientFrames() {
    $("#flow-client-results").hide();
    $("#flow-client-search-hide").attr('disabled', true);
    $("#flow-client-search-show").attr('disabled', true);
}

function showJobFrames() {
    $("#flow-job-results").show();
    $("#flow-job-search-hide").attr('disabled', false);
    $("#flow-job-search-show").attr('disabled', false);
    var row = $('tr[name="flow-row-job"]:first');
    row.addClass(SELECTED_ROW_CLASS);
    job_active_row = row.attr('id');
    $("#job_active_row").attr('value', job_active_row);

    if( job_active_row ) {
        loadJobItem(job_active_row, 0);
        $("#flow-job-registration").show();
    }
}

function hideJobFrames() {
    $("#flow-job-results").hide();
    $("#flow-job-search-hide").attr('disabled', true);
    $("#flow-job-search-show").attr('disabled', true);
    $("#id_status option[value=-1]").attr('selected', 'selected');
    $("#id_type option[value=-1]").attr('selected', 'selected');
    $("#flow-job-registration").hide();
}
//
// Search results pagination
//
function loadPage(mode, page) {
    switch (mode) {
    case 'client':
        loadClientPage(page);
        break;
    case 'job':
        loadJobPage(page);
        break;
    }
}

function loadClientPage(page) {
    display_loading(1);

    var value = $("#flow-client-search-input").val();
    var args = {'q':value, 'p':page};

    $.get("flow_client_loader", args, function(x) {
        var ob = $("#flow-client-main");
        ob.remove($('table'));
        ob.html(x);
        showClientFrames();
        hideJobFrames();
    }, "html");

    display_loading(0);
}

function loadJobPage(page) {
    display_loading(1);

    $.get("flow_job_loader", get_job_args(page), function(x) {
        var ob = $("#flow-job-main");
        ob.remove($('table'));
        ob.html(x);
        showJobFrames();
    }, "html");

    display_loading(0);
}
//
// Load active items
//
function loadPayStructureItem(row_id, show_loading) {
    if( !row_id ) return;
    if( show_loading ) display_loading(1);
    var id = row_id.split('-')[3];

    $.get("flow_paystructure_loader", {'pk__exact':id}, function(x) {
        $("#paystructure-container").html(x);
    }, "html");

    if( show_loading ) display_loading(0);
}

function loadJobItem(row_id, show_loading) {
    if( !row_id ) return;
    if( show_loading ) display_loading(1);
    var id = row_id.split('-')[3];

    $.get("flow_job_loader", {'pk__exact':id}, function(x) {
        $("#job-container").html(x);
        DateTimeShortcuts.init();
    }, "html");

    if( show_loading ) display_loading(0);
}
//
// Do main page actions (jQuery handlers)
//
$(document).ready(function() {
    //
    // 'Help' actions
    //
    $("*[id^='help']").toggle(function (e) {
        $("div[id^='help']").each(function() { $(this).show(); });
        $("#help-switch-image").attr('src', $("#help-switch-image").attr('src').replace('down', 'up'));
        $("#help-switch-title").html('Hide Help');

        e.stopPropagation();
    }, function (e) {
        $("div[id^='help']").each(function() { $(this).hide(); });
        $("#help-switch-image").attr('src', $("#help-switch-image").attr('src').replace('up', 'down'));
        $("#help-switch-title").html('Show Help');

        e.stopPropagation();
    });
    //
    // 'Keypress' actions
    //
    $("#flow-client-search-input").keypress(function(e) { 
        if(e.keyCode == '13') {
            e.preventDefault();
            loadClientPage(0);
        }
    });
    $("#flow-job-search-input").keypress(function(e) { 
        if(e.keyCode == '13') {
            e.preventDefault();
            loadJobPage(0);
        }
    });
    //
    // 'Go' actions
    //
    $("#flow-client-search-go").click(function() {
        loadClientPage(0);
    });
    $("#flow-job-search-go").click(function() {
        loadJobPage(0);
    });
    //
    // 'Clean' actions
    //
    $("#flow-client-search-clean").click(function() {
        $("#flow-client-search-input").attr('value', '').focus();
        client_active_row = '';
        $("#client_active_row").attr('value', client_active_row);
        job_active_row = '';
        $("#job_active_row").attr('value', job_active_row);
        hideClientFrames();
    });
    $("#flow-job-search-clean").click(function() {
        $("#flow-job-search-input").attr('value', '').focus();
        job_active_row = '';
        $("#job_active_row").attr('value', job_active_row);
        hideJobFrames();
    });
    //
    // 'Hide' actions
    //
    $("#flow-client-search-hide").click(function() {
        $("#flow-client-results").hide();
    });
    $("#flow-job-search-hide").click(function() {
        $("#flow-job-results").hide();
    });
    //
    // 'Show' actions
    //
    $("#flow-client-search-show").click(function() {
        $("#flow-client-results").show();
    });
    $("#flow-job-search-show").click(function() {
        $("#flow-job-results").show();
    });
    //
    // Active item click
    //
    $("*", document.body).click(function(e) {
        var ob = $(this);
        var id = ob.attr('id');
        var cids = id.split('-');

        get_active_rows();

        if( cids.length >= 3 && cids[0] == 'flow' && cids[2] == 'main' ) {
            aids = active_item.split('-');
            //
            // Open new page
            //
            if( aids.length >= 3 && aids[0] == 'flow' && aids[1] == 'page' ) {
                loadPage(aids[2], aids[3]);
            }
            //
            // Click on object's item
            //
            else if( aids.length >= 3 && aids[0] == 'flow' && aids[1] == 'row' ) {
                switch (aids[2]) {
                case 'client':
                    try {
                        var o = ( client_active_row ? $("#"+client_active_row) : $('tr[name="flow-row-client"]:first') );
                        if( o.hasClass(SELECTED_ROW_CLASS) ) o.removeClass(SELECTED_ROW_CLASS);
                    } catch (e) {}
                    var n = $("#"+active_item);
                    n.addClass(SELECTED_ROW_CLASS);

                    loadPayStructureItem(active_item, 0);
                    hideJobFrames();

                    client_active_row = active_item;
                    $("#client_active_row").attr('value', client_active_row);
                    break;
                case 'job':
                    try {
                        var o = ( job_active_row ? $("#"+job_active_row) : $('tr[name="flow-row-job"]:first') );
                        if( o.hasClass(SELECTED_ROW_CLASS) ) o.removeClass(SELECTED_ROW_CLASS);
                    } catch (e) {}
                    var n = $("#"+active_item);
                    n.addClass(SELECTED_ROW_CLASS);

                    loadJobItem(active_item, 0);

                    job_active_row = active_item;
                    $("#job_active_row").attr('value', job_active_row);
                    break;
                }
            }
        }
        
        e.stopPropagation();
    });
});
//
// Submit Job Flow actions
//
function SubmitJobItem(action) {
    if( !job_active_row || !action )
        return;

    display_loading(1);

    var args = get_job_args(0);
    var ob = $("#job-container");
    var aids = job_active_row.split('-');
    args['action'] = action;
    args['author'] = $("#author").val();
    args['pk'] = aids[3]

    $(":input[type='text']", ob).each(function(index) {
        args[$(this).attr('name')] = $(this).val();
    });
    $("select option:selected", ob).each(function(index) {
        args[$(this).parent().attr('name')] = $(this).attr('value');
    });
    $(":input[type='radio']:checked", ob).each(function(index) {
        args[$(this).attr('name')] = $(this).attr('value');
    });
    $(":input[type='checkbox']", ob).each(function(index) {
        args[$(this).attr('name')] = ( $(this).attr('checked') ? '1' : '' );
    });
    $(":input[type='hidden']", ob).each(function(index) {
        args[$(this).attr('name')] = $(this).val();
    });
/*
var s='';
for(var x in args) { s+=x+':'+args[x]+' '; } alert(s);
*/
    $.post("flow_job_loader", args, function(x) {
        var s = x.split('<!-- content-splitter //-->');
        var table_html = strip(s[0]);
        var item_html = strip(s[1]);

        if( table_html ) {
            var ob = $("#flow-job-main");
            ob.remove($('table'));
            ob.html(table_html);
        }
        if( item_html ) {
            var ob = $("#job-container");
            ob.remove($('table'));
            ob.html(item_html);
        }
        showJobFrames();
    }, "html");

    display_loading(0);
}

function doAmendment() {
    SubmitJobItem('amendment');
}

function doDuplicate() {
    SubmitJobItem('duplicate');
}

function doArchive() {
    SubmitJobItem('archive');
}

function doUpdate() {
    SubmitJobItem('update');
}

function doDelete() {
    if( confirm('Do you really wish to remove current item from the database?\nPlease, confirm.') ) SubmitJobItem('delete');
}
//
// Loader messenger
//
function display_loading( mode ) {
    if( mode == 1 ) $("#loading").fadeIn(500); else $("#loading").fadeOut();
}
//
// Form's submit & maintenance javascript utilities
//
var IsSubmitted = false;

function onSubmitForm( frm ) {
    if( IsSubmitted ) return false;
    IsSubmitted = true;
    disableForm(frm);
    return true;
}
  
function disableForm( frm ) {
    for( i = 0; i < frm.length; i++ ) {
        var tempobj = frm.elements[i];
        if ( tempobj.type == "submit" ) tempobj.disabled = true;
    }
}
  
function enableForm( frm ) {
    for( i = 0; i < frm.length; i++ ) {
        var tempobj = frm.elements[i];
        if ( tempobj.type == "submit" ) tempobj.disabled = false;
    }
}

function strip( s ) {
    return s.replace(/^\s+|\s+$/g, ''); // trim leading/trailing spaces
}
