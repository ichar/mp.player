$(window).unload(function() {
    var frm = document.forms[0];
    enableForm( frm );
})

function load_branches( ob, branch_selected, contact_selected ) {
    //
    // Download Branch/Contact field content
    //
    var value = $("option:selected", ob).val();
    if (value) $.get("loader", {'mode':'company2branches', 'id':value}, function(x) {
        $("#id_branch").html(x);
        if( branch_selected )
            $("#id_branch option[value="+branch_selected+"]").attr('selected', 'selected');
    }, "html");

    if (value) $.get("loader", {'mode':'company2contacts', 'id':value}, function(x) {
        $("#id_contact").html(x);
        if( contact_selected )
            $("#id_contact option[value="+contact_selected+"]").attr('selected', 'selected');
    }, "html");
}

function load_contacts( ob, contact_selected ) {
    //
    // Download Contact field content
    //
    var value = $("option:selected", ob).val();
    var mode = (ob.attr('id') == 'id_branch' ? 'branch2contacts' : 'company2contacts');
    if (value) $.get("loader", {'mode':mode, 'id':value}, function(x, contact_selected) {
        $("#id_contact").html(x);
        if( contact_selected )
            $("#id_contact option[value="+contact_selected+"]").attr('selected', 'selected');
    }, "html");
}

function InitForeignKeys() {
    //
    // Init foreign key fields state
    //
    var company = $("#id_company");
    var branch = $("#id_branch");
    var contact = $("#id_contact");

    var company_selected = $("option:selected", company).val();
    var branch_selected = $("option:selected", branch).val();
    var contact_selected = $("option:selected", contact).val();

    load_branches( company, branch_selected, contact_selected );
}

$(document).ready(function() {
    InitTimer( 0, '5-runtime', null );

    $("#id_company").change(function() { 
        display_loading(1);
        load_branches($(this), 0, 0);
        display_loading(0);
    });
/*
    $("#id_branch").change(function() {
        display_loading(1);
        load_contacts($("#id_company"), 0); // this
        display_loading(0);
    });
*/
    $("#id_0-id").change(function() {
        display_loading(1);
        var value = $("option:selected", this).val();
        if( value ) $.getJSON("loader", {'mode':'company2wizard', 'id':value}, function(x) {
            $.each(x, function(i,item) {
                 $("#id_0-country option[value="+item.fields.country+"]").attr('selected', 'selected');
                 $("#id_0-title").attr('value', item.fields.title);
                 $("#id_0-name").attr('value', item.fields.name);
                 $("#id_0-code").attr('value', item.fields.code);
                 $("#id_0-description").attr('value', item.fields.description);
                 $("#id_0-pk").attr('value', value);
            });
        }); else $("#id_0-pk").attr('value', '-1');
        display_loading(0);
    });

    $("#id_1-id").change(function() {
        display_loading(1);
        var value = $("option:selected", this).val();
        if( value ) $.getJSON("loader", {'mode':'branch2wizard', 'id':value}, function(x) {
            $.each(x, function(i,item) {
                 $("#id_1-country option[value="+item.fields.country+"]").attr('selected', 'selected');
                 $("#id_1-type option[value="+item.fields.type+"]").attr('selected', 'selected');
                 $("#id_1-IsHeadOffice").attr('checked', item.fields.IsHeadOffice);
                 $("#id_1-title").attr('value', item.fields.title);
                 $("#id_1-address").attr('value', item.fields.address);
                 $("#id_1-city").attr('value', item.fields.city);
                 $("#id_1-postcode").attr('value', item.fields.postcode);
                 $("#id_1-phone1").attr('value', item.fields.phone1);
                 $("#id_1-phone2").attr('value', item.fields.phone2);
                 $("#id_1-fax").attr('value', item.fields.fax);
                 $("#id_1-email").attr('value', item.fields.email);
                 $("#id_1-name").attr('value', item.fields.name);
                 $("#id_1-code").attr('value', item.fields.code);
                 $("#id_1-notes").attr('value', item.fields.notes);
                 $("#id_1-pay").attr('value', item.fields.pay);
                 $("#id_1-account").attr('value', item.fields.account);
                 $("#id_1-pk").attr('value', value);
            });
        }); else $("#id_1-pk").attr('value', '-1');
        display_loading(0);
    });

    $("#id_2-id").change(function() {
        display_loading(1);
        var value = $("option:selected", this).val();
        if( value ) $.getJSON("loader", {'mode':'contact2wizard', 'id':value}, function(x) {
            $.each(x, function(i,item) {
                //$("#id_0-country option:selected").removeAttr('selected');
                 $("#id_2-salutation option[value="+item.fields.salutation+"]").attr('selected', 'selected');
                 $("#id_2-title").attr('value', item.fields.title);
                 $("#id_2-name").attr('value', item.fields.name);
                 $("#id_2-phone").attr('value', item.fields.phone);
                 $("#id_2-mobile").attr('value', item.fields.mobile);
                 $("#id_2-email").attr('value', item.fields.email);
                 $("#id_2-description").attr('value', item.fields.description);
                 $("#id_2-IsManager").attr('checked', item.fields.IsManager);
                 $("#id_2-pk").attr('value', value);
            });
        }); else $("#id_2-pk").attr('value', '-1');
        display_loading(0);
    });

    $("#id_3-id").change(function() {
        display_loading(1);
        var value = $("option:selected", this).val();
        if( value ) $.getJSON("loader", {'mode':'paystructure2wizard', 'id':value}, function(x) {
            $.each(x, function(i,item) {
                 $("#id_3-type_"+item.fields.type).attr('checked', 'checked');
                 $("#id_3-title").attr('value', item.fields.title);
                 $("#id_3-fixed_fee").attr('value', item.fields.fixed_fee);
                 $("#id_3-price1").attr('value', item.fields.price1);
                 $("#id_3-price2").attr('value', item.fields.price2);
                 $("#id_3-price3").attr('value', item.fields.price3);
                 $("#id_3-price4").attr('value', item.fields.price4);
                 $("#id_3-price5").attr('value', item.fields.price5);
                 $("#id_3-price6").attr('value', item.fields.price6);
                 $("#id_3-price7").attr('value', item.fields.price7);
                 $("#id_3-price8").attr('value', item.fields.price8);
                 $("#id_3-price9").attr('value', item.fields.price9);
                 $("#id_3-price10").attr('value', item.fields.price10);
                 $("#id_3-max1").attr('value', item.fields.max1);
                 $("#id_3-max2").attr('value', item.fields.max2);
                 $("#id_3-max3").attr('value', item.fields.max3);
                 $("#id_3-max4").attr('value', item.fields.max4);
                 $("#id_3-max5").attr('value', item.fields.max5);
                 $("#id_3-max6").attr('value', item.fields.max6);
                 $("#id_3-max7").attr('value', item.fields.max7);
                 $("#id_3-max8").attr('value', item.fields.max8);
                 $("#id_3-max9").attr('value', item.fields.max9);
                 $("#id_3-max10").attr('value', item.fields.max10);
                 $("#id_3-pk").attr('value', value);
            });
        }); else $("#id_3-pk").attr('value', '-1');
        display_loading(0);
    });

    $("#id_4-id").change(function() {
        display_loading(1);
        var value = $("option:selected", this).val();
        if( value ) $.getJSON("loader", {'mode':'myob2wizard', 'id':value}, function(x) {
            $.each(x, function(i,item) {
                //$("#id_0-country option:selected").removeAttr('selected');
                 $("#id_4-type_"+item.fields.type).attr('checked', 'checked');
                 $("#id_4-title").attr('value', item.fields.title);
                 $("#id_4-myobaccount").attr('value', item.fields.myobaccount);
                 $("#id_4-myobvat").attr('value', item.fields.myobvat);
                 $("#id_4-myobcompany").attr('value', item.fields.myobcompany);
                 $("#id_4-myobquantity").attr('value', item.fields.myobquantity);
                 $("#id_4-pk").attr('value', value);
            });
        }); else $("#id_4-pk").attr('value', '-1');
        display_loading(0);
    });

    $("#id_5-id").change(function() {
        display_loading(1);
        var value = $("option:selected", this).val();
        if( value ) $.getJSON("loader", {'mode':'job2wizard', 'id':value}, function(x) {
            $.each(x, function(i,item) {
                 var received = (item.fields.received ? item.fields.received.split(' ') : new Array('',''));
                 var finished = (item.fields.finished ? item.fields.finished.split(' ') : new Array('',''));

                 InitTimer( 1, '5-runtime', item.fields.runtime );

                 $("#id_5-status option[value="+item.fields.status+"]").attr('selected', 'selected');
                 $("#id_5-user option[value="+item.fields.user+"]").attr('selected', 'selected');
                 $("#id_5-type_"+item.fields.type).attr('checked', 'checked');
                 $("#id_5-title").attr('value', item.fields.title);
                 $("#id_5-code").attr('value', item.fields.code);
                 $("#id_5-received_0").attr('value', received[0]);
                 $("#id_5-received_1").attr('value', received[1]);
                 $("#id_5-finished_0").attr('value', finished[0]);
                 $("#id_5-finished_1").attr('value', finished[1]);
                 $("#id_5-property").attr('value', item.fields.property);
                 $("#id_5-square").attr('value', item.fields.square);
                 $("#id_5-default").attr('value', item.fields['default']);
                 $("#id_5-price").attr('value', item.fields.price);
                 $("#id_5-calculated").attr('value', item.fields.calculated);
                 $("#id_5-IsAmendment").attr('checked', item.fields.IsAmendment);
                 $("#id_5-IsArchive").attr('checked', item.fields.IsArchive);
                 $("#id_5-pk").attr('value', value);
            });
        }); else $("#id_5-pk").attr('value', '-1');
        display_loading(0);
    });

    InitForeignKeys();
});
//
// New items functions
//
function new_company( prefix ) 
{
    var id = 'id_'+prefix;
    $("#"+id+"-id option[value='']").attr('selected', 'selected');
    $("#"+id+"-country option[value='']").attr('selected', 'selected');
    $("#"+id+"-title").attr('value', '');
    $("#"+id+"-name").attr('value', '');
    $("#"+id+"-code").attr('value', '');
    $("#"+id+"-description").attr('value', '');
    $("#"+id+"-pk").attr('value', '-1');
}

function new_branch( prefix ) 
{
    var id = 'id_'+prefix;
    $("#"+id+"-id option[value='']").attr('selected', 'selected');
    $("#"+id+"-country option[value='']").attr('selected', 'selected');
    $("#"+id+"-type option[value='']").attr('selected', 'selected');
    $("#"+id+"-IsHeadOffice").attr('checked', 0);
    $("#"+id+"-title").attr('value', '');
    $("#"+id+"-address").attr('value', '');
    $("#"+id+"-city").attr('value', '');
    $("#"+id+"-postcode").attr('value', '');
    $("#"+id+"-phone1").attr('value', '');
    $("#"+id+"-phone2").attr('value', '');
    $("#"+id+"-fax").attr('value', '');
    $("#"+id+"-email").attr('value', '');
    $("#"+id+"-name").attr('value', '');
    $("#"+id+"-code").attr('value', '');
    $("#"+id+"-notes").attr('value', '');
    $("#"+id+"-pay").attr('value', '-1');
    $("#"+id+"-account").attr('value', '-1');
    $("#"+id+"-pk").attr('value', '-1');
}

function new_contact( prefix ) 
{
    var id = 'id_'+prefix;
    $("#"+id+"-id option[value='']").attr('selected', 'selected');
    $("#"+id+"-salutation option[value='']").attr('selected', 'selected');
    $("#"+id+"-title").attr('value', '');
    $("#"+id+"-name").attr('value', '');
    $("#"+id+"-phone").attr('value', '');
    $("#"+id+"-mobile").attr('value', '');
    $("#"+id+"-email").attr('value', '');
    $("#"+id+"-description").attr('value', '');
    $("#"+id+"-IsManager").attr('checked', 0);
    $("#"+id+"-pk").attr('value', '-1');
}

function new_paystructure( prefix ) 
{
    var id = 'id_'+prefix;
    $("#"+id+"-id option[value='']").attr('selected', 'selected');
    $("#id_3-type_0").attr('checked', 'checked');
    $("#id_3-title").attr('value', 'PS: '+$("#id_0-title").val()+': '+$("#id_1-title").val());
    $("#id_3-fixed_fee").attr('value', '0.00');
    $("#id_3-price1").attr('value', '0.00');
    $("#id_3-price2").attr('value', '0.00');
    $("#id_3-price3").attr('value', '0.00');
    $("#id_3-price4").attr('value', '0.00');
    $("#id_3-price5").attr('value', '0.00');
    $("#id_3-price6").attr('value', '0.00');
    $("#id_3-price7").attr('value', '0.00');
    $("#id_3-price8").attr('value', '0.00');
    $("#id_3-price9").attr('value', '0.00');
    $("#id_3-price10").attr('value', '0.00');
    $("#id_3-max1").attr('value', '0.00');
    $("#id_3-max2").attr('value', '0.00');
    $("#id_3-max3").attr('value', '0.00');
    $("#id_3-max4").attr('value', '0.00');
    $("#id_3-max5").attr('value', '0.00');
    $("#id_3-max6").attr('value', '0.00');
    $("#id_3-max7").attr('value', '0.00');
    $("#id_3-max8").attr('value', '0.00');
    $("#id_3-max9").attr('value', '0.00');
    $("#id_3-max10").attr('value', '0.00');
    $("#"+id+"-pk").attr('value', '-1');
}

function new_myob( prefix ) 
{
    var id = 'id_'+prefix;
    $("#"+id+"-id option[value='']").attr('selected', 'selected');
    $("#"+id+"-type_0").attr('checked', 'checked');
    $("#"+id+"-title").attr('value', 'MYOB: '+$("#id_0-title").val()+': '+$("#id_1-title").val());
    $("#"+id+"-myobaccount").attr('value', '');
    $("#"+id+"-myobvat").attr('value', 'S');
    $("#"+id+"-myobcompany").attr('value', '');
    $("#"+id+"-myobquantity").attr('value', '1');
    $("#"+id+"-pk").attr('value', '-1');
}

function new_job( prefix ) 
{
    var id = 'id_'+prefix;
    $("#"+id+"-id option[value='']").attr('selected', 'selected');
    $("#"+id+"-status option[value='']").attr('selected', 'selected');
    $("#"+id+"-user option[value='']").attr('selected', 'selected');
    $("#"+id+"-type_0").attr('checked', 'checked');
    $("#"+id+"-title").attr('value', '');
    $("#"+id+"-code").attr('value', '');
    $("#"+id+"-received_0").attr('value', '');
    $("#"+id+"-received_1").attr('value', '');
    $("#"+id+"-finished_0").attr('value', '');
    $("#"+id+"-finished_1").attr('value', '');
    $("#"+id+"-property").attr('value', '0');
    $("#"+id+"-square").attr('value', '');
    $("#"+id+"-default").attr('value', '0.00');
    $("#"+id+"-price").attr('value', '0.00');
    $("#"+id+"-calculated").attr('value', '0.00');
    $("#"+id+"-IsAmendment").attr('checked', 0);
    $("#"+id+"-IsArchive").attr('checked', 0);
    $("#"+id+"-pk").attr('value', '-1');

    InitTimer( 0, '5-runtime', null );
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
