"use strict";
/**
 *
 * Initializes account management pages for users and orgs
 *
 * @requires jquery
 * @requires base.js
 * @requires forms.js
 *
 * @param form
 *  outer most keys are for the tabs nav
 *  inner objects are is each property of the entity, its form type, value type, val...
 *  form types include section, name, number, select
 *
 * @param def - default type -- 'default' is a reserved word
 * @param type -- 'org' / 'user' geo...
 */

JUMO.Manage = {
    parent: JUMO,
    postJSON: JUMO.Util.postJSON,
    initialize: function(params) {
        this.setupLocation();
        if (params !== undefined && params.multiLocation) {
            this.initMultiLocation();
        }
    },

    setupLocation: function(location) {
        var this_ = this;
        var locationDiv = jQuery('#id_location_input');

        // use user location to query the yahoo places api
        if (location !== undefined && location.length > 0) {
            locationDiv.val(location);                          
        }

        if (locationDiv !== undefined && locationDiv.length > 0) {
            this.parent.FormMaker.makeLocationDiv(locationDiv, this);        
            this.parent.FormMaker.getLocationForString(encodeURIComponent(location),
                                                       function(v) { this_.setLocationVal(v[0]); },
                                                       function(v) { /* do nothing on fail console.log(v) */ });
        }
    },                  
    
    setLocationVal: function(val) {
        jQuery('#id_location_data').val(JSON.stringify(val));
    },

    initMultiLocation: function() {
        this.multiLocationDiv = jQuery('#id_working_locations');
        this.parent.FormMaker.MultiLocationForm.initialize(this.multiLocationDiv);
    },

    showDeactivatePopup: function(){
        var this_ = this;
        var popup = this.parent.Modules.Popup.showPopupForJobj(jQuery('#templates .deactiviate_popup'), 380);

        // TODO: make this into a form that posts
        popup.find('.change_settings').click(function(evt) {
                                                 this_.parent.Modules.Popup.hidePopup(popup);
                                                 this_.parent.Util.showhideTabs('notifications', this_.formTypes);
                                             });


        popup.find('.close').click(function(evt) {
                                       this_.parent.Modules.Popup.hidePopup(popup);
                                   });
    },

    enableSubmit: function(jObj){
        jObj.removeClass('disabled').parent().removeClass('disabled').css('opacity', 1).find('.loading').remove();
    }
};
