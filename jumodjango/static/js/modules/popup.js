"use strict";
/**
 * widget for displaying notifications to the user
 *
 * needs to be initialized with a div
 *
 * @requires jquery
 *
 * compiled with base.js
 */

JUMO.Modules.Popup = {
    parent: JUMO,
    initialize: function(div, orgInfoDiv) {
        this.mainDiv = jQuery(div);
        this.orgInfoPopup = jQuery(orgInfoDiv).clone().hide().appendTo('#page-content');
        this.setupCommitmentPopup();
        this.setupFollowPopup();
        this.setupFollowerPopups();
        this.setupCloseEvent();
        return this;
    },

    setupFollowPopup: function() {
        var this_ = this;
        jQuery('.follow, .unfollow').live('click', function(e) {
                                              e.preventDefault();
                                              var jObj = jQuery(this);
                                              if (jObj.hasClass("login")) {
                                                  this_.showLoginCreateAccountPopup();
                                              } else {
                                                  JUMO.Util.ajaxPost({                                                                             
                                                                         url: jObj.attr("data-url"),
                                                                         data: {},
                                                                         success: function(data) {
                                                                             jObj.parents(".follow_button").replaceWith(data["result"]["button"]);
                                                                         }
                                                                     });
                                              }
                                          });
    },

    setupCommitmentPopup: function() {
        var this_ = this;
        jQuery(".delete_commitment").live('click', function(e) {
                                              e.preventDefault();
                                              var jObj = jQuery(this);
                                              var form = jObj.parents("form");
                                              var url = jObj.attr("data-url");
                                              JUMO.Util.ajaxPost({  url: url,
                                                                    data: form.serialize(),
                                                                    success: function(data) {
                                                                        if (data !== undefined && data.result !== undefined) {
                                                                            jObj.parents(".commitment_button").replaceWith(data.result.button);
                                                                            // Do the other stuff here with json of actions: data["result"]["actions"]
                                                                        }
                                                                    }
                                                                 });
                                          });

        jQuery('.section.photos li').click(function(e) {
                                               var jObj = jQuery(this);
                                               var fullsize = jObj.attr('data-fullsize');
                                               var caption = jObj.attr('data-caption');
                                               this_.showLargePhotoPopup(fullsize, caption);
                                           });

        jQuery(".create_commitment").live('click', function(e) {
                                              if (this_.parent.user && this_.parent.user.id) {
                                                  e.preventDefault();
                                                  var jObj = jQuery(this);
                                                  var form = jObj.parents("form");
                                                  var url = jObj.attr("data-url");
                                                  var withPopup = jObj.attr("data-with_popup"); // this is either a 0 or 1 -- not a bool
                                                  JUMO.Util.ajaxPost({  url: url,
                                                                        data: form.serialize(),
                                                                        success: function(data) {
                                                                            if (data !== undefined && data.result !== undefined) {
                                                                                jObj.parents(".commitment_button").replaceWith(data.result.button);
                                                                                
                                                                                if (withPopup > 0) {
                                                                                    this_.showActionPopup( data.result.actions );
                                                                                }
                                                                            }
                                                                        }
                                                                     });
                                              } else {
                                                  this_.showLoginCreateAccountPopup();
                                              }
                                          });

        jQuery(".view_actions").live('click', function(e) {
                                         e.preventDefault();
                                         var jObj = jQuery(this);
                                         var url = jObj.attr("data-url");
                                         JUMO.Util.ajaxGet({  url: url,
                                                              success: function(data) {
                                                                  if (data !== undefined && data.result !== undefined) {
                                                                      this_.showActionPopup( data.result.html );
                                                                  }
                                                              }
                                                           });
                                     });        
    },
    
    setupFollowerPopups: function() {
        var this_ = this;
        jQuery('#committed_users, #user_followers, #user_following, #issues_following, #orgs_following')
            .live('click', function(e) {
                      e.preventDefault();
                      var reqUrl = jQuery(this).attr('data-url');
                      var title = jQuery(this).attr('data-title') || "";
                      this_.showFollowersPopup(reqUrl, title);
                  });
    },
    
    showFollowersPopup: function(reqUrl, heading) {
        var this_ = this;
        var reqInterval = 19;
        var popup = this_.showPopupForJobj( jQuery('#templates .entitylist_popup'), 420 );
        
        var loadData = function(url, params) {
            popup.find('.rounded_box').append('<div class="loading-row"></div>');
            JUMO.Util.ajaxGet({ url: reqUrl,
                                data: {start: popup.data("start"), end: popup.data("end") },
                                success: jQuery.proxy(onLoadSuccess, this_)
                              });
        };
        
        var onLoadSuccess = function(response) {
            var markup = response["result"]["html"];
            var hasMore = (response["result"]["has_more"] === true);
            // remove loader if there
            popup.find('.loading-row').remove();
            // append our response
            popup.find('.rounded_box').append(markup);
            // if there's more, setup our handler again
            if(hasMore) {
                popup.find('.rounded_box')
                    .asyncScroller("reset", {pollInterval: 2000, bottomHitArea: 200})
                    .one("scrollEnd.asyncScroller", function(e) {
                             var target = $(this);
                             popup
                                 .data("start", (popup.data("start") + reqInterval)+1 )
                                 .data("end", (popup.data("start") + reqInterval) );
                             loadData( reqUrl );
                             target.asyncScroller("destroy");
                         })
                    .append('<div class="loading-row"></div>');
            }
        };
        
        // set popup heading
        popup
            .find('.heading')
            .html( heading );
        // initialize first request
        popup.data("start", 0).data("end", reqInterval);
        loadData( reqUrl );
    },
    
    showLargePhotoPopup: function(imgsrc, caption) {
        var popup = jQuery('#templates .photo_viewer_popup');
        popup
            .find('.fullsize').attr('src', imgsrc).end()
            .find('.caption').text(caption);

        this.showPopupForJobj(popup);
    },

    showActionPopup: function( actionsHTML ) {
        var this_ = this;
        var popup = this.showPopupForJobj(jQuery('#templates .action_popup'), 500);
        popup.find('.sm_info').html( actionsHTML );
    },

    setupCloseEvent: function(){
        var this_ = this;
        jQuery('.submit_spacer .button, .close', jQuery('#notification'))
            .live('click', function(evt){
                      return this_.hidePopup(jQuery(this));
                  });

        jQuery("#popup_box")
            .live('click keyup', function(evt){
                      this_.hidePopup(jQuery(this));
                      evt.stopPropagation();
                      return false;
                  });
    },

    // corrects offsets for popups in a standard and consistent way
    getPos: function(top, left, jObj, width) {
	    if (top === undefined) {
 	        top = jObj.position().top;
	        left = jObj.position().left;
	    }

	    if (left + width > document.width) {
	        left = document.width - width  - 15;
	    }

	    top += jObj.height() + 20;
        left -= 12;

	    return { top: top, left: left };
    },

    showUploadUserPhoto:function() {
        var this_ = this;
        var popup = this.showPopupForJobj(jQuery('#templates .photo_upload_popup'), 420);

        popup.find('.close').click(function(){
                                       this_.hidePopup(popup);
                                   });
    },

    showSuccessPopup: function(text, pos){
        var note = jQuery('#notification').addClass('success top');
        note.text(text)
            .css({width:'80px'})
            .slideDown(300, function(){
                           setTimeout(function() { note.slideUp(300); }, 3000);
                       });

        this.parent.Util.matchDivPosition(note, pos);
    },

    getPopupPosition: function(width, winWidth, padding) {
        return {
            width: width + "px",
            top: jQuery(window).scrollTop() + 75,
            left: ((winWidth/2) - (width/2) - padding/2) + "px",
            position:'absolute',
            'z-index':11,
            padding:padding
        };
    },

    showPopupForJobj: function(jObj, width, padding) {
        var width = width || 420;
        var padding = padding || 30;
        var winWidth = jQuery(window).width();
        var winHeight = jQuery(window).height();

        this.hidePageContent();

        return jQuery('#notification').removeClass()
            .addClass('popup notification')
            .html('')
            .css(this.getPopupPosition(width, winWidth, padding))
            .append(jObj.clone())  // boo -- lose all listeners here :(
            .show();
    },

    showFBConnectPopup: function() {
        var this_ = this;
        var popup = this.showPopupForJobj(jQuery('#templates .fb_connect_login'), 420);
        popup.find('#fb_login').click(function(){ this_.parent.Util.fbLogin(jQuery(this)); });
    },

    showLoginPopup: function() {
        var popup = this.showPopupForJobj(jQuery('#templates .login'), 420);
        popup.find('#login').click(function(){ window.location = "/login"; });
    },

    showLoginCreateAccountPopup: function() {
        var this_ = this;
        var popup = this.showPopupForJobj(jQuery('#templates .loginCreateAccount'), 420);
        popup.find('#login').click(function(){ window.location = "/login"; });
        popup.find('#fb_login').click(function(){ this_.parent.Util.fbLogin(jQuery(this)); });
    },

    showErrorPopup: function(text) {
        var popup = this.showPopupForJobj(jQuery('#templates .error_popup'), 420);
        popup.find('.error_text').text(text);
    },

    hidePageContent: function() {
        this.pageOverlay = jQuery("<div id=\"popup_box\"></div")
            .css({
                     position:'fixed',
                     width:jQuery(window).width() + "px",
                     height:jQuery(window).height() + "px",
                     top:'0px',
                     left:'0px',
                     background:'#f3f3f3',
                     opacity:'0.9',
                     'z-index':10
                 });

        jQuery('body').append(this.pageOverlay);
    },

    hideLoginPopup: function(){
        jQuery('#notification').removeClass().hide().css({position:'absolute'});
        this.pageOverlay.remove();
    },

    hideOrgInfoPopup: function(){
        this.orgInfoPopup.hide();
    },

    hidePopup: function(div) {
        jQuery('#notification').removeClass().hide().css({position:'absolute'});
        jQuery("#popup_box").remove();

        if (this.parent.Modules.Popup.pageOverlay) {
            this.parent.Modules.Popup.pageOverlay.remove();
        } else {
            jQuery(div).parent().parent().hide();
        }
    },

    show:function() {
        this.mainDiv.show();
    },

    hide: function() {
        this.mainDiv.hide();
    }
};


(function( $ ){
     // ---------- TEMP LOGGING
     /*
      var logger = {
      log: function(o) {
      if(console && console.log) {
      //console.log.apply(this, [prefix].concat(arguments) ); // why is this illegal invocation?! fu chrome/safari
      console.log(prefix, o);
      }
      }
      };
      */
     // ---------- End TEMP LOGGING
     
     var hasScrolled = false;
     var defaults = {
         bottomHitArea: 50,
         pollInterval: 1000
     };
     
     var checkEnd = function() {
         //logger.log('checkEnd(), verify scope: ');
         //logger.log(this);
         var o = $(this);
         var totalHeight = 0;
         // "scrollHeight" is not supported in some IE, so check property first    
         if( o.get(0).scrollHeight && typeof(o.get(0).scrollHeight === "number") ) {
             totalHeight = o.get(0).scrollHeight;
         } else { // determine height through adding up children
             o.children().each(function(){totalHeight += $(this).outerHeight() });
         }
         //logger.log("totalHeight ==== scrollHeight: " + (o.get(0).scrollHeight === totalHeight) ); // nice, always seems to be the same in browers supporting scrollHeight
         var atEnd = ( totalHeight - (o.innerHeight() + o.scrollTop()) ) < defaults.bottomHitArea;
         //logger.log("at end? " + atEnd);
         
         return atEnd;
     };
     
     var startPoll = function(dur) {
         //logger.log('startPoll()');
         var this_ = this;
         var pollId = setTimeout( 
             function(){
                 //logger.log('interval function');
                 clearTimeout(pollId);
                 if( $.proxy(checkEnd, this_)() || (!hasScrolled) ) {
                     $(this_).trigger('scrollEnd.asyncScroller');   
                 } else {
                     $.proxy(startPoll, this_)(dur);
                 }
             },
             dur);
     };
     
     var clearPoll = function(id) {
         //logger.log('clearPoll(), id: '+id);
         clearTimeout(id);
     };
     
     var methods = {
         init: function(params) {
             var this_ = this;
             //logger.log("init()");
             if (params) { 
                 $.extend( defaults, params );
             }
             //logger.log("merged params:");
             //logger.log(defaults);
             
             return this.each(function(){
                                  // unbind any existing listener and start timer after first scroll
                                  //logger.log("attaching scroll listener");
                                  $(this).unbind("scroll").one("scroll", function(o){
                                                                   //logger.log("scroll handler removing listener");
                                                                   hasScrolled = true;
                                                                   $(this).unbind("scroll"); // unecessary, but be safe
                                                                   // HACK: no matter the setting, don't let poll interval happen more than every quarter second                    
                                                                   $.proxy(startPoll, this_)( Math.max(defaults.pollInterval, 250) );
                                                               });
                              });
         },
         destroy: function() {
             //logger.log("destroy()");
             return this.each(function(){
                                  // remove any events in our namespace
                                  $(this).unbind('.asyncScroller');
                                  clearTimeout();
                              });
         },
         reset: function(params) {
             //logger.log("reset()");
             var this_ = this;
             return this.each(function(){
                                  $.proxy(methods.init, this_)(params);
                              });
         }
     };
     $.fn.asyncScroller = function( method ) {
         if ( methods[method] ) {
             return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
         } else if ( typeof method === 'object' || ! method ) {
             return methods.init.apply( this, arguments );
         } else {
             $.error( method + ' does not exist on jQuery.asyncScroller' );
         }  
     };
 })( jQuery );
