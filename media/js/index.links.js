//
// Clickable main menu items
//
SPLITTER = ':';

$(document).ready(function() {
    //
    // Main menu items
    //
    $(".index-list").mouseover(function() {
        $(this).addClass('index-list-selected');
        $("span[class^='info']", this).each(function() { $(this).attr('style', 'color:white;'); });
    }).mouseout(function() {
        $(this).removeClass('index-list-selected');
        $("span[class^='info']", this).each(function() { $(this).attr('style', ''); });
    });

    $(".index-list").click(function(e) {
        window.location=$(this).find("a").attr("href");
        e.stopPropagation();
        return false;
    });
    //
    //  Actions box
    //
    $("img[id^='actions']").click(function (e) {
        $ToggleBox($(this), "actions_", null, e);
    });
});
