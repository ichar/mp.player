// **************************************
// JOB FORM JS PATCH /jobform-20161023.js
// --------------------------------------
// Version: 1.0
// Date: 23-10-2016

function $_init_20161023() {
    var ob = $("#id_status")[0];
    if (ob != null) {
        var top = ob.getBoundingClientRect().top + $(window)['scrollTop']();
        var left = ob.getBoundingClientRect().left + $(window)['scrollLeft']();
        
        //alert(top+':'+left);

        $(".edged").css('top', top-3).css('left', left+350);
    }
}

$(function() 
{
    $_init_20161023();
});
