//
// Report columns list updater
//
$(document).ready(function() {
    $("#id_report").change(function() {
        var value = $("option:selected", this).val();
        $.get("loader", {'mode':'report2columns', 'id':value}, function(x) {
            var ob = $("#report_selected_columns");
            ob.remove($('table'));
            ob.html(x);
        }, "html");
    });
});