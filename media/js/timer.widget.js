//
// Timer widgets
//
function SetTimer( name, value )
{
    if( !value) value = 0;

    if( value > 0 ) {
        var D = Math.round(value/1440);
        if( D*1440 > value) D = D - 1;
        var H = Math.round((value - D*1440)/60);
        if( D*1440 + H*60 > value) H = H - 1;
        var M = value - D*1440 - H*60;
    } else {
        var D = 0;
        var H = 0;
        var M = 0;
    }

    var odays  = document.getElementById('id_'+name+'_days');
    var ohours = document.getElementById('id_'+name+'_hours');
    var omins  = document.getElementById('id_'+name+'_mins');

    if( typeof(odays)  == 'object' ) odays.value  = D.toString();
    if( typeof(ohours) == 'object' ) ohours.value = H.toString();
    if( typeof(omins)  == 'object' ) omins.value  = M.toString();

    document.getElementById('id_'+name).value = (value ? value.toString() : '');
}

function InitTimer( mode, name, value ) 
{
    if( !name ) return;
    if( mode == 0 ) {              // init, else update
        // update from response
        var obj = document.getElementById('id_'+name);
        if( typeof(obj) != 'object' || obj == null ) return;
        if( value == null ) value = (obj.value ? parseInt(obj.value) : 0);
    }

    SetTimer( name, value );
}

function EvalTimer( mode, name, interval )
{
    var odays  = document.getElementById('id_'+name+'_days');
    var ohours = document.getElementById('id_'+name+'_hours');
    var omins  = document.getElementById('id_'+name+'_mins');

    var D = (typeof(odays)  == 'object' ? parseInt(odays.value)  : 0);
    var H = (typeof(ohours) == 'object' ? parseInt(ohours.value) : 0);
    var M = (typeof(ohours) == 'object' ? parseInt(omins.value)  : 0);

    if( mode == 'up' ) {
        if( M >= 60 - interval ) {  // +1 hour
            M = M + interval - 60;
            if( H >= 23 ) {         // +1 day
                H = 0;
                if( D == 30 ) return;
                D = D + 1;
            } else {
                H = H + 1;
            }
        } else {
            M = M + interval;
        }
    } else {
        if( M < interval ) {        // -1 hour
            M = 60 - interval + M;
            if( H == 0 ) {          // -1 day
                H = 23;
                if( D == 0 ) return;
                D = D - 1;
            } else {
                H = H - 1;
            }
        } else {
            M = M - interval;
        }
    }

    value = D*1440 + H*60 + M;

    SetTimer( name, value );
}
