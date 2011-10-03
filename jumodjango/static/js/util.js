"use strict";
/**
 * GENERAL UTLS
 */

JUMO.Util =  {
    parent: JUMO,
    popup : JUMO.Modules.Popup,
    defaultErrorMessage: 'An unknown error has occured.',
    sentenceCase: function() {
        return this.toLowerCase().replace(/^(.)|\s(.)/g,
                                          function($1) { return $1.toUpperCase(); });
    },

    parseUrlHash: function(urlHash) {
        if (urlHash !== undefined && this.entity !== undefined) {
            return jQuery('#' + id).addClass('highlight');
        }

        if (this.getUrlParameterByName('new_user')) { jQuery('.new_user').show(); } ;
    },

    clearInputs: function() {
        jQuery("input[type=text]").val("");
    },
    
    /**
     * modified from http://stackoverflow.com/questions/1068834/object-comparison-in-javascript
     */
    areObjectsEquivalent: function(x, y) {
        for (var p in x) {
            if(typeof(y[p]) == 'undefined') { return false; }
        }

        for (p in x) {
            if (x[p]) {
                switch(typeof(x[p])) {
                case 'object':
                    if (!this.areObjectsEquivalent(x[p], y[p])) { return false; }; break;
                case 'function':
                    if (typeof(y[p]) == 'undefined' || (p != 'equals' && x[p].toString() != y[p].toString())) { return false; }; break;
                default:
                    if (x[p] != y[p]) { return false; }
                }
            } else {
                if (y[p]) {  return false;  }
            }
        }

        for (p in y) {
            if (typeof(x[p]) == 'undefined') { return false; }
        }

        return true;
    },

    clone:function(c,dest,except) {
	    if (dest === undefined) { dest = {}; }
	    for (var v in c) {
	        if (except === undefined || except.indexOf(v) < 0) {
		        dest[v] = c[v];
	        }
	    }
	    return dest;
    },

    uniqueArray: function(a) {
        /**
         * uniques elements in an array
         * reguards 1st encountered element as original
         */
        var r = [];
        o:for(var i = 0, n = a.length; i < n; i++) {
            for(var x = 0, y = r.length; x < y; x++){
                if(r[x]==a[i]) continue o;
            }
            r[r.length] = a[i];
        }
        return r;
    },

    //+ Jonas Raoni Soares Silva
    //@ http://jsfromhell.com/math/is-point-in-poly [rev. #0]
    isPointInPoly: function(poly, pt){
        for(var c = false, i = -1, l = poly.length, j = l - 1; ++i < l; j = i)
            ((poly[i].y <= pt.y && pt.y < poly[j].y) || (poly[j].y <= pt.y && pt.y < poly[i].y))
            && (pt.x < (poly[j].x - poly[i].x) * (pt.y - poly[i].y) / (poly[j].y - poly[i].y) + poly[i].x)
            && (c = !c);
        return c;
    },

    jObjToPoly: function(jObj){
        var p = jObj.offset();
        var width = jObj.width();
        var height = jObj.height();

        if (p && p.left) {
            return [{
		                x: p.left - 1,
		                y: p.top
	                }, {
		                x: p.left + width + 15,
		                y: p.top
	                }, {
		                x: p.left + width + 15,
		                y: p.top + height
	                }, {
		                x: p.left - 1,
		                y: p.top + height
	                }, {
		                x: p.left - 1,
		                y: p.top
	                }];
        } return [{}];
    },

    str_trim : function(stringToTrim) {
        if (stringToTrim !== undefined) {
            return stringToTrim.replace(/^\s+|\s+$/g,"");
        }
        return stringToTrim;
    },
    trim : function(string) {
        if (!string){
            return "";
        } else if (string.trim !== undefined) {
            return string.trim();
        } else {
            return this.str_trim(string);
        }
    },
    replaceAll:function(str,what,withwhat) {
        var lastidx = 0;
        while (lastidx >= 0) {
            lastidx = str.indexOf(what,lastidx + withwhat.length);
            str = str.substring(0,lastidx)+str.substring(lastidx).replace(what,withwhat);
        }
        return str;
    },
    isDateLike: function () {
        for (var i = 0; i < arguments.length; i++) {
            var o = arguments[i];
            if (typeof(o) != "object" || o === null || typeof(o.getTime) != 'function') {
                return false;
            }
        }
        return true;
    },
    isArrayLike: function () {
        for (var i = 0; i < arguments.length; i++) {
            var o = arguments[i];
            var typ = typeof(o);
            if ((typ != 'object' && !(typ == 'function' && typeof(o.item) == 'function')) || o === null || typeof(o.length) != 'number' ) {
                return false;
            }
        }
        return true;
    },

    isNumeric: function(input){
        var val = String(input).replace('\n', "").replace('\r', "").replace('\t', "").replace(' ', '');
        return ((input - 0) == input && input.length > 0);
    },

    sum:function(lst) {
        var add = function(x,y) { if (!y) { return x; } return x + y; };
        return lst.reduce(add,0);
    },

    handleFollowSuccess: function(data, jObj, actionType) {
        jObj.removeClass(actionType);
        if (actionType == 'follow') {
            if (jObj.attr('src')) {
                jObj.addClass('unfollow').attr({src: "/static/img/unfollow_small.png"});
            } else if (jObj.find('img').length > 0) {
                jObj.removeClass('disabled')
                    .addClass('unfollow')
                    .find('img').attr({src:"/static/img/unfollow_img.png"});
            } else {
                jObj.addClass('unfollow').text('Unfollow');
            }
        } else {
            if (jObj.attr('src')) {
                jObj.addClass('follow').attr({src: "/static/img/follow_small.png"});
            } else if (jObj.find('img').length > 0) {
                jObj.removeClass('disabled')
                    .addClass('follow')
                    .find('img').attr({src: "/static/img/follow_img.png"});
            } else {
                jObj.addClass('follow').text('Follow');
            }
        }
    },

    handleFollowFail: function(response, jObj) {
        // todo -- make the popup do something in relation to the jObj passed in
        this.handelError(response);
    },

    handleError: function(response) {
        this.popup.showErrorPopup(this.getParsedErrorText(response));
    },

    getParsedErrorText: function(response) {
        var text = "There was an error processing your request. Please try submitting again.";

        if (response && response.error) {
            text = '(' + response.error_code + ") " + response.error;
        }
        return text;
    },

    addLoadingImg: function(jObj){
        jObj.append('<img class=\"loading\" src="/static/img/ajax-loader.gif" />').css({opacity:0.5});
    },

    removeLoadingImg: function(jObj){
        jObj.css({opacity:1}).parent().find('.loading, .sm_loading').remove();
    },

    addSmallLoadingImg: function(jObj){
        jObj.append('<img class=\"sm_loading\" src="/static/img/ajax-loader_sm.gif" />').css({opacity:0.5});
    },

    followUnfollow: function(ent_id, ent_type, user_id, jObj, thumb_location) {
        var this_ = this;
        var actionType = jObj.hasClass('unfollow') ? 'unfollow' : 'follow';

        try {
            this.addLoadingImg(jObj);
        } catch (x) {/* hide */ }

        this.postJSON('user/action/follow/', {
                          items: ent_id,
                          item_type: ent_type,
                          user_id: user_id,
                          action: actionType
                      }, function(data) {
                          this_.removeLoadingImg(jObj);

                          if (data.result !== undefined) {
                              this_.parent.Modules.Tracking.trackAction(actionType, {
                                                                    "Followed ID":   ent_id,
                                                                    "Followed Type": ent_type
                                                                });

                              return this_.handleFollowSuccess(data, jObj, actionType);
                          }
                          return this_.handleFollowFail(data, jObj);
                      });
    },

    postJSONandDisplayLoading: function(url, args, callback, formJobj, submitJobj) {
        var this_ = this;
        var loadingDiv = this.showLoading(formJobj, submitJobj);

        this.postJSON(url, args, callback, function() {
                          this_.hideLoading(formJobj, submitJobj, loadingDiv);
                      });
    },

    save: function(jObj, cont) {
        try {
            if (jObj.hasClass('disabled')) { return false; }

            this.addLoadingImg(jObj.parent());

            Checker.disableSubmit(jObj);
            Checker.clearError(jObj);

            cont();

        } catch (e) {
            jObj.removeClass('disabled');
            Checker.showError(jObj, JSON.stringify(e));
            this.removeLoadingImg(jObj.parent());
        }
    },

    showHTTPError: function(XMLHttpRequest, textStatus, errorThrown) {
        // enable submit
        jQuery('.button.disabled').removeClass('disabled');
        
        // need to reference JUMO here as 'this' gets overritten by the scope of the containing function in jQuery.ajax
        if (XMLHttpRequest && XMLHttpRequest.status == 404) {
            return;
        } else if (XMLHttpRequest && XMLHttpRequest.status == 502) {
            JUMO.Modules.Popup.showErrorPopup('Error: you place an incorrectly formed request');
        } else {
            JUMO.Modules.Popup.showErrorPopup('An unknown error has occured.');
        }
    },

    /**
     *  @param postCallback is used by postJSONandDisplayLoading to return form to normal state
     */
    postJSON: function(url, args, callback, postCallback, errorCont) {
        var this_ = this;
        var getCookie = function(name) {
            var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
            return r ? r[1] : undefined;
        };

        args._xsrf = getCookie("_xsrf");
        jQuery.ajax({
                        type: 'POST',
                        url: '/json/v1/' + url,
                        data: args,
                        success: function(data){
                            try {
                                callback(eval(data));
                                if (postCallback) {
                                    postCallback();
                                }
                            } catch (x) {
                                this_.popup.showErrorPopup(JSON.stringify(x));
                            }
                        },
                        // this wraps the passed errorCont so it is consistent w/ JUMO implementation
                        error: errorCont ? function(){ errorCont(this_.defaultErrorMessage); jQuery('.button.disabled').removeClass('disabled'); } : this.showHTTPError,
                        dataType: 'json'
                    });
    },
    
    ajaxPost: function(params) {
        return this.ajaxRequest( params, "POST" );
    },
    
    ajaxGet: function(params) {
        return this.ajaxRequest( params, "GET" );
    },
    
    ajaxRequest: function(params, type) {
        var this_ = this;
        
        // default settings for ajax request, overriden by params
        var defaults = {
            type: type,
            data: {},
            dataType: 'json',
            error: jQuery.proxy( this_.handleAjaxError, this_ )
        };
        // merge passed in params with our defaults
        var reqCfg = jQuery.extend(defaults, params);
        
         // add xsrf cookie to request data for POST requests
        if( type == "POST" ) {        
            var getCookie = function(name) {
                var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
                return r ? r[1] : undefined;
            };
            reqCfg.data._xsrf = getCookie("_xsrf");
        }
        
        // return req object
        return jQuery.ajax( reqCfg );
    },
    
    handleAjaxError: function(xhr, textStatus, errorThrown) {
        var code = parseInt(xhr.status, 10);
        var errTxt = "There was an error processing your request. Please try submitting again.";
        switch(code) {
            case 404:
                //break;
            case 200:
                //break;
            case 500: 
                //break;
            default:
                errTxt += " (code: "+code+")";
                break;
        }
        this.popup.showErrorPopup( errTxt );
    },

    initPlaceholder: function(jObj) {
        return jObj.val(jObj.attr('placeholder')).addClass('placeholder');
    },

    fixPlaceHolder: function(jObj, type) {
        var val = this.trim(jObj.val()) || this.trim(jObj.text());
        var placeholder = this.trim(jObj.attr('placeholder'));

        if (type == 'focusin') {
            jObj.removeClass('placeholder');
        }

        if (placeholder == val || (!val && type == 'focus')){
            jObj.val("").removeClass('placeholder');
        } else if ((!val && type == 'focusout') || (!val && type == 'blur')) {
            jObj.val(placeholder).addClass('placeholder');
        }
    },

    getFormVal: function(jObj) {
        var val = this.trim(jObj.val());
        var placeholder = this.trim(jObj.attr('placeholder'));

        return val == placeholder ? "" : val;
    },

    linkifyTweet: function(text){
        return text.replace(/(^|\s)(@\w+)/gm, '$1<a href="http://twitter.com/$2">$2</a>');
    },

    showhideTabs: function(type, formTypes) {
        type = type.replace(' selected', "");
        type = type.split(' ')[0];
        formTypes.map(function(t) {
                          var jObj = jQuery('#' + t);
                          if (t != type) {
                              jQuery('.' + t).removeClass('selected');
                              jObj.hide(0);
                          } else {
                              jQuery('.' + t).addClass('selected');
                              jQuery(window).scrollTop(0);
                              jObj.show();
                          }
                      });
    },

    getUrlParameterByName: function( name ) {
        name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
        var regexS = "[\\?&]"+name+"=([^&#]*)";
        var regex = new RegExp( regexS );
        var results = regex.exec( window.location.href );
        if (results == null ) {
            return "";
        } else {
            return decodeURIComponent(results[1].replace(/\+/g, " "));
        }
    },

    reverse: function(strToReverse) {
        var strRev = new String;
        var i = strToReverse.length;
        while (i--)
            strRev += strToReverse.charAt(i);
        return strRev;
    },

    resizeIt: function(jObj) {
        var str = jObj.val();
        var cols = jObj.attr('cols');
        var linecount = 0;

        str.split("\n").map(function(l) {
					            linecount += 1 + Math.floor( l.length / cols ); // take into account long lines
                            });

        jObj.attr({rows: linecount > 3 ? linecount : 3 });
    },

    resizeItSmall: function(jObj) {
        var str = jObj.val();
        var cols = jObj.attr('cols');
        var linecount = 0;

        str.split("\n").map(function(l) {
					            linecount += 1 + Math.floor( l.length / cols ); // take into account long lines
                            });

        jObj.attr({rows: linecount });
    },

    makeCharCountDiv: function(jObj, counter, max) {
        var minCharactersBeforeWarning = 50;
        var shown = false;

        jObj.bind('keyup click blur focus change paste', function() {
                      var num = max - jQuery(this).val().length;
                      if (num < minCharactersBeforeWarning) {
                          if (!shown) { counter.show(); }

                          shown = true;
                          counter.html(num);
                          return;
                      } else if (shown) {
                          counter.hide();
                      }

                      shown = false;
                  });
    },

    /** Begin Comment form validation
     * note: modified subset of forms.js so that we dont have to import all of forms.js into all pages
     */

    _stripHtml: function(text) {
        return jQuery('<div>' + text + '</div>').text();
    },

    stripHtml: function(text) {
        var t = this._stripHtml(text);

        if (this._stripHtml('<\n>') !== '&lt;\n&gt;') {
            return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        }
        return t;
    },

    formatString: function(val) {
        return this.stripHtml(val)
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("<", "(")
            .replace(">", ")")
            .replace("“", "\"")
            .replace("”", "\"")
            .replace("'", "'")
            .replace("‘", "'")
            .replace("’", "'")
            .replace("–", "-")
            .replace(">", ")")
            .replace("\\", "/")
            .replace(/"(?=\w|$)/g, "&#8220;")
            .replace(/\b"/g, "&#8221;");
    },

    isValidString: function(value) {
        // the last character here is weird non ascii (’) -- it appears when copying and pasting from websites
        return /^[\w \d \. \, \' \" \: \@ \; \? \- \# \– \& \( \) \! \s \: \; \- \! \r \+ \/ \* \— \’]+$/i.test(value);
    },

    /**
     * matches neu div to old div position w/ a bit of margin
     * this way margin is consistent across the ui
     *
     * @param neu needs to be a jObj
     * @param pos needs to be a jObj
     */
    matchDivPosition: function(neu, pos) {
        neu.css({'top': pos.top + 17, 'left' : pos.left -25 });
    },

    showLoading: function(jObj, clickedJobj) {
        jObj.click(function(event){
                       event.stopPropagation();
                       return false;
                   });
        jObj.fadeTo('slow', 0.5);
        return jObj.after("<img class=\"loading\" src='/static/img/loading.gif>");
    },

    getSmallImageForEntity: function(entity) {
        var url;
        if (entity.img_url) {
            url = entity.img_url;
        } else if (entity.facebook_id) {
            url = 'http://graph.facebook.com/' + entity.facebook_id + '/picture?type=square';
        }

        return '<img src="' + url + '" class="sm_image" />';
    },

    hideLoading: function(jObj, clickedObj, loadingDiv) {
        jObj.click(function(event){
                       event.stopPropagation();
                       return true;
                   });

        jObj.fadeTo('slow', 1);
        loadingDiv.remove();
    },

    getUrlVars: function(){
        var vars = [], hash;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for (var ii = 0; ii < hashes.length; ii++) {
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }
        return vars;
    },

    /* todo -- make work for textarea, input and contenteditabledivs  */
    getInputVal: function(jObj) {
        return this.trim(jObj.val());
    },

    getUrlVar: function(name){
        return this.getUrlVars()[name];
    },

    getHash: function(){
        return (window.location.hash !== undefined && window.location.hash.length > 0) ? window.location.hash.slice().replace("#", "") : undefined;
    },

    checkUserExists: function(fbid, cont, errorcont) {
        this.postJSON('user/fbid_check/', {"fbid": fbid}, function(response) {
                          if (Number(response.error_code) < 1 && response.result !== undefined) {
                              if (response.result.exists > 0) {
                                  errorcont('Your Facebook account is already using Jumo. Please <a href="/login">login</a>');
                              } else {
                                  cont();
                              }
                          } else {
                              errorcont(response.error_code);
                          }
                      });
    },

    showYoutubeVideo: function(appendToId, divID, youtubeID, width, height) {
        var params = {             
            allowfullscreen: "true",
	        play: "true",
	        loop:"false",
			menu:"true"
		};

        var w = width ? String(width) : "200"; 
        var h = height ? String(height) : "160"; 

        var atts = { id: divID };
        return swfobject.embedSWF("http://www.youtube.com/v/" + youtubeID + "?enablejsapi=1&playerapiid=ytplayer&autoplay=1&allowfullscreen=true&version=3&autohide=1&showinfo=0",
                                  appendToId, w, h, "8", null, null, params, atts);
    },
    
    fbLogin: function(jObj) {
        var this_ = this;
        FB.login(function(response) {
                     if (response.session !== undefined && response.session !== null && response.session.uid !== undefined) {
                         this_.checkUserExists(response.session.uid, function(response) {
                                                   window.location = '/setup';
                                               }, function(text) {
                                                   // todo -- make an error div for fbid fail
                                                   // todo make this switch to a login form?
                                                   jObj.parent().find('.notification').show().html(text);
                                               });
                     } else {
                         jObj.parent().find('.notification').show().html('Your Facebook account is already using Jumo. Please <a href="/login"><b>login</b></a>');
                     }
                 }, { perms: 'publish_stream, offline_access' });
    },
    
    capitalize: function(text){
        return text.replace( /(^|\s)([a-z])/g , function(m,p1,p2){ return p1+p2.toUpperCase(); } );
    }
};
