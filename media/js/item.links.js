//
// Clickable main menu items
//
$(document).ready(function() {
    //
    // Object's Change List items
    //
    $(".item-list").mouseover(function() {
        $(this).addClass('item-list-selected');
        $("span[class^='rendered']", this).each(function() { $(this).attr('style', 'color:white;'); });
    }).mouseout(function() {
        $(this).removeClass('item-list-selected');
        $("span[class^='rendered']", this).each(function() { $(this).attr('style', ''); });
    });
});
