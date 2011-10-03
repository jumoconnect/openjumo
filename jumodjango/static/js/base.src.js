"use strict";
/**
 * Main JUMO file
 *
 * JUMO
 * JUMO.Util
 * JUMO.Modules
 *             .Search
 *             .Popup
 *
 * @requires jquery
 * @requires popup.js
 *
 * COMPILE SCRIPT: java -jar compiler.jar --js=base.src.js --js=lib.js --js=util.js --js=modules/feed.js --js=modules/popup.js --js=modules/tracking.js --js=modules/publisher.js --js_output_file=base.js
 */

var JUMO = {
    timesSearched: 0,
    Modules: {},
    /**
     * initialize differently based on whether user is signed in and
     * whether the current page is an entity page
     * todo: page type!
     *
     * @param params {userId, userName, userHandle, userAgeGroup, userGender, ot(???), +
     *            if entity -- entityID, entityType, entityName, entityHandle}
     */
    initialize: function(params) {
        this.browserIsIE = jQuery.browser.msie;
        this.isErrorPage = params.isErrorPage;
        this.isEntityPage = params.entityID ? true : false;
        this.isSignedIn = params.userName ? true : false;

        // if user signed in
        if (this.isSignedIn) {
            this.user = {
                id:   params.userID,
                name: params.userName,
                ageGroup: params.userAgeGroup,
                gender: params.userGender,
                fbAccessToken: params.fbAccessToken
            };
            this.setupTopNav();
        }

        if (this.isEntityPage) {
            this.entity = {
                name:   params.entityName,
                id:     params.entityID
            };
        }

        this.Modules.Popup.initialize('#templates .notification', '#templates .org_hoverbox');
        this.Modules.Search.initialize();
        this.setupMouseEvents();
        this.Util.parseUrlHash(this.Util.getHash());
    },

    setupMouseEvents: function() {
        var this_ = this;

        // fb login
        jQuery('#create_account_button .button').click(function() {
                                                           this_.Util.fbLogin(jQuery(this));
                                                       });

        // following-followers popup
        jQuery('#page-content .showall').click(function(evt) {
                                                   var name = jQuery(this).attr('id').replace('#', "");
                                                   var jObj = jQuery('#templates .' + name);
                                                   this_.Modules.Popup.showPopupForJobj(jObj);                                                       
                                               });
        if (this.isEntityPage) {
            jQuery('.cs .youtube_thumb').click(function(evt){
                                                   var videoID = jQuery(this).attr('id');
                                                   this_.Util.showYoutubeVideo(videoID, videoID, videoID.replace('youtube_', ''));
                                               });
        }
    },

    setupTopNav: function() {
        var this_ = this;
        var nav = jQuery('#nav_account_tab');
        var navMenu = jQuery('#nav_menu');

        // account slide down thing
        nav.click(function(){
                      navMenu.toggle();
                      jQuery(this).toggleClass('active');
                  });

        jQuery('body').click(function(evt) {
                                 if (navMenu.is(':visible')){
                                     var clickPt = {
                                         x:evt.clientX,
                                         y:evt.clientY
                                     };
                                     var navPoly = this_.Util.jObjToPoly(nav);
                                     var boxPoly = this_.Util.jObjToPoly(navMenu);
                                     if (!this_.Util.isPointInPoly(navPoly, clickPt) && !this_.Util.isPointInPoly(boxPoly, clickPt)) {
                                         navMenu.hide();
                                         nav.removeClass('active');
                                     }
                                 }
                             });
    }
};


/*
 * todo: DELETE and do this on the server
 */
var JUMOFB = {
    parent: JUMO,
    updateToken: function(token) {
        this.parent.user.fbAccessToken = token;
        $.ajax({
                   url:  '/json/v1/user/fbot_update',
                   data: {'ot' : token },
                   type: 'post',
                   success: function(data, ts) {},
                   error: function(xhr, ts, et) {}
               });
    },

    checkAuth: function(callback, failCallback) {
        this.callback = callback;
        var this_ = this;
        if (this.parent.user) {
            FB.getLoginStatus(function(response) {
                                  if (response.session == null) {
                                      // this is a duplicate of fbLogin in util.js
                                      return FB.login(function(response) {
                                                          if (response.session.access_token != this_.parent.user.fbAccessToken) {
                                                              JUMOFB.updateToken(response.session.access_token);
                                                              this_.callback();
                                                              return;
                                                          }
                                                      }, { perms:'publish_stream, offline_access, user_birthday' });
                                  } else if (response.session.access_token != this_.parent.user.fbAccessToken) {
                                      JUMOFB.updateToken(response.session.access_token);
                                  }
                                  this_.callback();
                              });
        }
    },

    displayFbName: function() {
        var this_ = this;

        if (typeof(FB) === 'undefined') { return; }

        FB.api('/me', function(response) {
                   jQuery('#fb_name').text(response.first_name + ' ' + response.last_name);
               });
    },

    setupFBLogin: function(uid, accessToken) {
        var this_ = this;

        var login = function(userid, token) {
            jQuery.ajax({
                            url: '/json/v1/user/fb_login',
                            data: {
                                'id' : userid,
                                'ot' : token
                            },
                            type: 'post',
                            success: function(data, ts) {
                                var redirect = jQuery('input[name=redirect_to]');
                                if (redirect.length > 0) {
                                    window.location = redirect.val();
                                } else {
                                    window.location = '/';
                                }
                            },
                            error: function(xhr, ts, et) { }
                        });
        };

        jQuery('#fb_single_signin').click(function() {
                                              jQuery('#fb_single_signin').before('<div class="loading-row"></div>');
                                              if (uid) {
                                                  login(uid, accessToken);
                                              } else {
                                                  FB.login(function(response) {
                                                               if (response.session) {
                                                                   login(response.session.uid, response.session.access_token);
                                                               } else {
                                                                   // user cancelled login
                                                                   jQuery('#fb_single_signin').siblings(".loading-row").remove();
                                                               }
                                                           });
                                              }
                                          });
    },

    displayLogin: function() {
        var this_ = this;

        if (typeof(FB) === 'undefined') { return; }

        FB.getLoginStatus(function(response) {
                              if (response.session) {
                                  var response_ = response;
                                  var uid = response.session.uid;
                                  var accessToken = response.session.access_token;

                                  jQuery('#fb_login').show();
                                  jQuery('#fb_profile_pic').attr('src', 'http://graph.facebook.com/' + uid + '/picture?type=square');

                                  this_.displayFbName();
                                  this_.setupFBLogin(uid, accessToken);
                              } else {
                                  this_.setupFBLogin(undefined, accessToken);
                              }
                          });
    }
};
