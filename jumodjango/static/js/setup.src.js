"use strict";
/**
 * Initializes new-user account creation
 *
 * @requires jquery
 * @requires base.js
 *
 * compile script: java -jar compiler.jar --js=setup.src.js --js_output_file=setup.js
 */

var Setup = {
    parent:JUMO,
    popup: JUMO.Modules.Popup,
    initialize: function() {
        this.user = {};
        this.setupMouseEvts();
        this.setupUserLocation();
    },
    setupMouseEvts: function() {
        var this_ = this;
        jQuery('#change_account').click(function() {
                                            FB.logout();
                                            this_.parent.Util.fbLogin(jQuery(this).parent());
                                        });

        jQuery('#fb_signup').click(function() {
                                            this_.parent.Util.fbLogin(jQuery(this).parent());
                                        });
    },

    // helpers -- see manage.js
    setupUserLocation: function() {
        this.parent.FormMaker.makeLocationDiv(jQuery('#id_location_input'), this);
    },

    setLocationVal: function(val, jObj) {
        var this_ = this;
        if (!val || val.length < 1){ return; }
        jQuery('#id_location_data').val(JSON.stringify(val));
    },

    setupUserFromFacebookMe: function(response){
        if (!this.user) { this.user = {}; }

        this.user.first_name = response.name ? response.name.split(' ')[0] : "";
        this.user.last_name = response.name ? response.name.split(' ').slice(1, response.name.split(' ').length).join(' ') : "";
	    this.user.fbid = response.id ? String(response.id) : "";
	    this.user.email = response.email || "";
	    this.user.bio = response.bio || "";
	    this.user.gender = response.gender || "";
	    this.user.fb_access_token = FB.getSession().access_token;

        if (this.user.email && jQuery('#id_email').val().length < 1) {
	        jQuery('#id_email').val(this.user.email);
        }
        if (this.user.first_name && jQuery('#id_first_name').val().length < 1) {
	        jQuery('#id_first_name').val(this.user.first_name);
        }
        if (this.user.last_name && jQuery('#id_last_name').val().length < 1) {
	        jQuery('#id_last_name').val(this.user.last_name);
        }
	    jQuery('#id_fb_access_token').val(this.user.fb_access_token);
	    jQuery('#id_fbid').val(this.user.fbid);
	    jQuery('#id_bio').val(this.user.bio);
	    jQuery('.profile_img_cont, .post_to_fb').show();

        this.showUserImage(this.user.fbid);

	    if (this.user.gender == 'male') {
	        jQuery('input[type=radio]')[0].click();
	    } else if (this.user.gender == 'female') {
	        jQuery('input[type=radio]')[1].click();
	    }
    },

    showUserImage: function(fb_id) {
        if (fb_id !== undefined) {
            var imgURL = "http://graph.facebook.com/" + String(fb_id) + "/picture?type=square";
            jQuery('.profile_img').attr('src', imgURL).show();
        }
    },
    trackFunnel: function(name, values) { this.parent.Modules.Tracking.trackFunnel("New User: " + name, values); }
};
