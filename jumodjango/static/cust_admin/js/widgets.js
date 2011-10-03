//Custom popup script for selecting items to populate our custome foreign key widget.
function custShowRelatedObjectLookupPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^lookup_/, '');
    name = id_to_windowname(name);
    var href;
    if (triggeringLink.href.search(/\?/) >= 0) {
        href = triggeringLink.href + '&pop=1&ext_pop=1&';
    } else {
        href = triggeringLink.href + '?pop=1&ext_pop=1&';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function custDismissRelatedLookupPopup(win, chosenId, chosenName) {
    var name = windowname_to_id(win.name);
    document.getElementById(name).value = chosenId;
    document.getElementById("name_"+name).onclick = function(){return false;};
    document.getElementById("name_"+name).text = chosenName;
    document.getElementById("name_"+name).innerText = chosenName;

    win.close();
}
