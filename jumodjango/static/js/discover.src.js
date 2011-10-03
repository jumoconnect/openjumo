"use strict";
/**
 * Initializes discover
 *
 * @requires jquery
 * @requires base.js
 * @requires data/recommended_orgs.js
 * 
 * compile script: java -jar compiler.jar --js=discover.src.js --js_output_file=discover.js
 */

JUMO.Discover = {
    speed: 10,
    tagMax: 1,
    numRows: 3,
    numColumns: 3,
    maxOrgsPerRow: 2,
    defaultOrgWidth: 167,
    parent: JUMO,
    popup: JUMO.Modules.Popup,
    initialize: function(recommendedIssues, following, userlocation) {
        if (this.user === undefined) { this.user = {}; }
        this.trackFunnel('Account Created');
        this.panel= 2;
        this.recommendedIssues = this.randomiseRecommendedOrgs(recommendedIssues);
        this._init_following = JUMO.Util.clone(following, []);
        this.following = following;

        this.setupMouseEvts();

        if (JUMO.user && JUMO.user.id) {
            this.user = JUMO.user;
            this._gotoSecondPanel(JUMO.user.name);
            this.doNotShowPopup = true;

            if (userlocation && this.parent.FormMaker.locationToString(userlocation)) {
                this.locationVal = userlocation;
                this.getNearbyOrgs(this.locationVal);
            }
        }
    },

    trackFunnel: function(name, values) { JUMO.Modules.Tracking.trackFunnel("New User: " + name, values); },

    /**
     *
     *
     * begin mouse events
     */
    clickEntity:function(event, jObj) {
        var item = this._getItem(jObj.attr('data-id'), jObj.find('.name').text() || jObj.text(), jObj.attr('data-type'), jObj);
        var followingDiv = jObj.find('.notinterested');

        if (jObj.parent().attr('id') == 'rec_types') {
            return;

        } else if (followingDiv.hasClass('checked')) {
            followingDiv.removeClass('checked');

            followingDiv.removeClass('disabled');

            followingDiv.find('span:first').css({'background-position': '0 0'});
            followingDiv.find('span:last').text('click to follow');
            followingDiv.find('input:first').attr('checked', false);
            this.removeFollowing(item);

        } else {
            followingDiv.addClass('checked');
            followingDiv.addClass('disabled');

            followingDiv.find('span:first').css({'background-position': '0 -50px'});
            followingDiv.find('span:last').text('following');

            followingDiv.find('input:first').attr('checked', true);
            this.addFollowing(item);
        }
    },

    setupMouseEvts: function() {
        var this_ = this;
        jQuery('#get_started').click(function(){ this_.getStarted(jQuery(this)); });


        jQuery('li.org', jQuery('#issues')[0]).live('click', function(event) {
                                                        var jObj = jQuery(this);
                                                        this_.clickEntity(event, jObj);
                                                    });

        jQuery('#change_account').click(function(){
                                            FB.logout();
                                            JUMO.Util.fbLogin(jQuery(this).parent());
                                        });
        
        jQuery('#next').click(function(){
                                  /** survey panel */
                                  if (this_.panel == 2) {
                                      // reset survey results 
                                      this_.user.new_user_survey = {};
                                      jQuery('#survey .survey_row').each(function(index, item) {
                                                                             var jObj = jQuery(item);

                                                                             var name = jObj.find('input:eq(0)').attr('name');
                                                                             var val = jObj.find(':checked').length > 0 ? jObj.find(':checked').val() : 0;

                                                                             this_.user.new_user_survey[name] = val;
                                                                         });

                                      var yesVotes = Object.keys(this_.user.new_user_survey).filter(function(key){ return this_.user.new_user_survey[key] > 0; });

                                      if (!this_.user.new_user_survey || yesVotes.length < 1 ) { // TODO -- need a better test here
                                          return this_.showError('please select at least one option');
                                      }

                                      // update display
                                      jQuery('#next').text('Done!');
                                      jQuery('#currentstep').text('3/3').show();
                                      
                                      this_.hideError();
                                      this_.trackFunnel('Selected Issue Areas', this_.user.new_user_survey);
                                      this_.gotoThirdPanel(jQuery(this), function() { jQuery('#step li:eq(2)').addClass('filled');  });
                                      
                                      /**  org panel */
                                  } else if (this_.panel == 3) {
                                      
                                      if (!this_.following) {
                                          return this_.showError('please follow at least one issue or project');
                                      } else {
                                          var orgs = this_.following.filter(function(item) { return item.type == 'org'; }).map(function(item){ return item.id; });
                                          if (orgs.length < 1) {
                                              return this_.showError('please follow at least one issue or project');
                                          }
                                      }
                                      
                                      this_.hideError();
                                      return this_.followSelectedEntities(function(){
                                                                              if (this_.doNotShowPopup) {
                                                                                  window.location = "/";
                                                                              } else {
                                                                                  window.location = "/?new_user=true";
                                                                              }
                                                                          }, jQuery(this));

                                  }
                              });
    },
    /** end mouse events */


    /**
     *
     *
     * begin -- BUILD recommended orgs and issues
     */
    buildRecommendedIssuesAndOrgs: function(categories){
        var this_ = this;
        var itemsToAppend = [];
        var issueJobj = jQuery('#issues ul.rec');

        issueJobj.html('');

        var topInterests = categories.filter(function(category){
                                                 return this_.user.new_user_survey[category.name] &&
                                                     this_.user.new_user_survey[category.name] > 1;
                                             });

        var medInterests = categories.filter(function(category){
                                                 return this_.user.new_user_survey[category.name] &&
                                                     this_.user.new_user_survey[category.name] > 0 &&
                                                     this_.user.new_user_survey[category.name] < 2;
                                             });

        jQuery.fn.append.apply(issueJobj,
                               [topInterests, medInterests].map(function(interest){
                                                                    if (interest !== undefined && interest.length > 0) {
                                                                        return interest.map(function(issue){
                                                                                                if (issue !== undefined) {
                                                                                                    return this_.buildRecommendedOrgRow(issue.issues, issue.name);
                                                                                                }
                                                                                                return false;
                                                                                            });
                                                                    }
                                                                    return false;
                                                                }).reduce(function(a,b) { return a.concat(b); }, []));

        this.buildNearbyInterests(this.nearbyOrgs, issueJobj);
    },


    buildNearbyInterests: function(orgs, jObj){
        if (!this.nearbyOrgs){ return; }

        var this_ = this;
        var newObj = jQuery('#templates .follow_row').clone();

        // edit heading
        newObj.find('.head .name')
            .html(this.getWhiteImageForIssue('nearby') + 'Near Me');

        // make location div
        var location = this.parent.FormMaker.locationToString(this.locationVal);
        newObj.find('.head').append("<div class=\"locationdiv\">my location: <input value='" + location + "'></input></div>");
        this.parent.FormMaker.makeLocationDiv(newObj.find('.head input'), this);

        // special case style
        newObj.find('.issues').hide().end()
            .find('.orgs').css({
                                   'border-left':'0px',
                                   width:'99.7%',
                                   left:'0px'
                               });

        this.drawNearbyOrgs(newObj, orgs);

        newObj.find('.org_container').css({width:this.getOrgContainerWidth(170, orgs.length) });

        newObj.find('.right_arrow').click(function(event){
                                              this_.animateOrgsRight({name:'nearby', orgs:this_.nearbyOrgs}, newObj);
                                          });
        jObj.append(newObj);
    },

    drawNearbyOrgs: function(newObj, orgs){
        var this_ = this;

        // append orgs on the right
        if (orgs && orgs.length > 0) {
            newObj.find('.follow_boxes li.orgs ul').html('');
            jQuery.fn.append.apply(newObj.find('.follow_boxes li.orgs ul'),
                                   orgs.map(function(org){
                                                var jObj = this_.buildRecommendedOrg(org, 'nearby');
                                                if (jObj) {
                                                    jObj.css({width:'170px'});
                                                    return jObj;
                                                }
                                            }) );
        }
    },


    changeOrgSelectTab: function(jObj, issue, appendedOrgs) {
        var this_ = this;
        var parent = jObj.parent().parent().parent();

        if (jObj.hasClass('selected')){ return; }

        jObj.parent().find('li').removeClass('selected');
        jObj.addClass('selected');

        parent.find('.org_container').css({left:'0px'});

        this.animateHideOrgs(parent,
                             function(cont) {
                                 var ul = parent.find('.orgs ul');
                                 jQuery.fn.append.apply(ul, issue.orgs.map(function(org){
                                                                               return this_.buildRecommendedOrg(org, issue.name);
                                                                           }) );
                                 cont(ul);
                                 ul.css({width: (this_.defaultOrgWidth * issue.orgs.length + 10) + "px"});
                             });
    },

    animateHideOrgs: function(jObj, cont) {
        var speed = 200;
        var orgsDiv = jObj.find('.orgs');
        var width = jObj.find('.orgs').width() < 506 ? "506px" : jObj.find('.orgs').width();

        orgsDiv.animate({width:0}, speed, function() {
                            var animatingDude = jQuery(this);
                            animatingDude.find('.org').remove();

                            orgsDiv.css({display:'inline-block'});

                            cont(function(ul){
                                     animatingDude.animate({width: width}, speed);
                                 });
                        });
    },

    buildRecommendedIssue: function(issue){
        var this_ = this;
        return jQuery('#templates .issue').clone()
            .attr({'data-id': issue.id, 'data-type':'issue' })
            .html(issue.name)
            .click(function(evt){
                       // change tab
                       this_.changeOrgSelectTab(jQuery(this), issue, 0);
                   });
    },

    getFollowHTML: function(isFollowed) {
        return '<input class="styled" type="checkbox"' +
            (isFollowed ? 'checked' : '') + '/>' +
            '<span>' + (isFollowed ? 'following' : 'click to follow') + '</span>';
    },

    _buildRecommendedOrg: function(org, issuename){
        var this_ = this;
        var isFollowed = this.isOrgBeingFollowed(org.id);
        var followHTML = this.getFollowHTML(isFollowed);

        /* hiding more_info as all i have are the old ids not new ones */

        return jQuery('#templates .org').clone()
            .attr({'data-id': org.id, 'data-type':'org' })
            .addClass(isFollowed ? 'checked': "")
            .find('.more_info').attr({'data-id': org.id}).hide().end()
            .find('.name').text(org.name).end()
            .find('.orgphoto').attr({ src: this._getOrgImgUrl(org) }).end()
            .find('.tags').text(this._getTags(org.tags, issuename)).end()
            .find('.notinterested').html(followHTML).addClass(isFollowed ? 'disabled' : '').end()
            .find('.follow').click(function(evt){
                                       this_.followOrgAndRefresh(org, jQuery(this));
                                   }).end()
            .find('.notInterested').click(function(evt){
                                              this_.followOrgAndRefresh(org, jQuery(this));
                                          })
            .end();
    },

    buildRecommendedOrg: function(org, issuename){
        this.recommendedItems.push(org.id);
        return this._buildRecommendedOrg(org, issuename);
    },

    buildRecommendedOrgRow: function(issues, name){
        var this_ = this;
        var jObj = jQuery('#templates .follow_row').clone();

        this.recommendedItems = [];
        this.appendedOrgs = 0;
        this.extraOrgs = {};

        jObj.find('.head .name').html(this.getWhiteImageForIssue(name) + name);

        // append issues on the left
        jQuery.fn.append.apply(jObj.find('.follow_boxes li.issues ul'),
                               issues.slice(0,5).map(function(issue){
                                                         if (this_.recommendedItems.indexOf(issue.id) < 0) {
                                                             this_.recommendedItems.push(issue.id);
                                                             return this_.buildRecommendedIssue(issue);
                                                         }
                                                         return false;
                                                     }));

        // append orgs on the right
        if (issues !== undefined && issues[0] !== undefined) {
            jQuery.fn.append.apply(jObj.find('.follow_boxes li.orgs ul'),
                                   issues[0].orgs.map(function(org){
                                                          return this_.buildRecommendedOrg(org, issues[0].name);
                                                      }) );
            jObj.find('.follow_boxes li.orgs ul').css({width: this.getOrgContainerWidth(this_.defaultOrgWidth, issues[0].orgs.length)});
        }

        jObj.find('.issues .issue:eq(0)').addClass('selected');

        jObj.find('.right_arrow').click(function(event){
                                            //this_.refreshRecommendedOrgs(issues, jObj);
                                            this_.animateOrgsRight(issues, jObj);
                                        });
        return jObj;
    },

    getOrgContainerWidth: function(width, num){
        return ((width * num) + 10) + "px";
    },

    animateOrgsRight: function(issues, jObj){
        var this_ = this;

        var speed = 300;
        var orgsDiv = jObj.find('.orgs');
        var orgsContainer = jObj.find('.org_container');
        var leftPos = Number(orgsContainer.css('left').replace('px', ""));
        var width = jObj.find('.orgs').width() < 506 ? 506 : jObj.find('.orgs').width();

        var pos = leftPos - width;

        if (Math.abs(pos) >= orgsContainer.width()){
            pos = 0;
        }

        orgsContainer.animate({left:pos + 'px'}, speed);
    },

    refreshRecommendedOrgs: function(issues, jObj, currentIssueParam, max, width){
        var this_ = this;

        var currentIssueId = jObj.find('.issue.selected').attr('data-id');
        var currentIssueName = jObj.find('.issue.selected').text();
        var lastDisplayedOrgId = jObj.find('.org:last').attr("data-id");

        var currentIssue = currentIssueParam || issues.filter(function(issue){ return issue.id == currentIssueId; })[0];
        var currentIndex = currentIssue.orgs.map(function(org){ return org.id; }).indexOf(lastDisplayedOrgId);
        var currentOrgs = currentIssue.orgs;

        this.animateHideOrgs(jObj,
                             function(cont) {
                                 var ul = jObj.find('.orgs ul');
                                 jQuery.fn.append.apply(ul, currentOrgs.map(function(org){
                                                                                var obj = this_.buildRecommendedOrg(org, currentIssueName);
                                                                                if (width){ obj.css({width:width}); }

                                                                                return obj;
                                                                            }) );
                                 cont(ul);
                             });
    },

    getNearbyOrgs: function(location, cont){
        var this_ = this;

        if (!location) { return; }

        JUMO.Util.postJSON('org/fetch_centroid/', {
                               lat: location.latitude,
                               lon: location.longitude,
                               limit: 8
                           }, function(response) {
                               if (Number(response.error_code) < 1 && response.result) {
                                   this_.nearbyOrgs = JSON.parse(response.result);

                                   if (cont){ cont(this_.nearbyOrgs); }
                               }
                           });
    },
    /** end rec org and issue display */

    /**
     *
     *
     * begin -- SURVEY
     */
    buildSurveyRow: function(name) {
        var this_ = this;

        return jQuery('#templates .survey_row').clone()
            .find('.text').html(this.getImageForIssue(name.toLowerCase()) + name)
            .end()
            .find("input").attr({name: name})
            .end();
    },

    buildSurvey: function(recommendedIssues){
        var this_ = this;

        jQuery.fn.append.apply(jQuery('#survey ul.rec'),
                               recommendedIssues.map(function(issue){
                                                         if (issue !== undefined && issue.name !== undefined) {
                                                             return this_.buildSurveyRow(issue.name);
                                                         }
                                                     })
                              );
    },


    /**
     *
     *
     *
     * begin -- NAV -- from panel to panel
     */
    setStepUI: function(stepNum){
        jQuery('#step li').removeClass('filled');
        jQuery('#step li:eq(' + (stepNum - 2) + ')').addClass('checked');
        jQuery('#step li:eq(' + (stepNum - 1) + ')').removeClass('checked').addClass('filled');
    },

    /** helper for going to second panel from 1st panel */
    _gotoSecondPanel: function(username) {
        this.gotoSecondPanel(function() { jQuery('#step li:eq(1)').addClass('filled');});
    },

    gotoSecondPanel: function(cont) {
        var this_ = this;

        this.panel = 2;
        //this.freezeDocHeight();
        cont();

        this.setStepUI(this.panel);
    },

    gotoThirdPanel: function(jObj, cont) {
        var this_ = this;

        this.panel = 3;
        //this.freezeDocHeight();
        cont();

        this.setStepUI(this.panel);
        this.buildRecommendedIssuesAndOrgs(this.recommendedIssues);

        jQuery('#signup, #survey').animate({width: 'hide'}, this.speed, function(){
                                               jQuery('#issues')
                                                   .animate({width: 'show'}, this_.speed, function() {
                                                                jQuery(window).scrollTop(0);
                                                                //this_.unFreezeDocHeight();
                                                            });
                                           });
        jQuery('#following').show();
    },

    _setupLocationForThirdPanel: function(doNotAppendReults){
        // nmake sure this only runs 1x
        if (this.setupLocationForThirdPanel) { return; }

        var location = this.parent.FormMaker.locationToString(this.locationVal);

        this.parent.FormMaker.makeLocationDiv(jQuery('#location_org input'), this);
        this.setLocationVal(this.locationVal, jQuery('#location_org input'), doNotAppendReults);

        this.setupLocationForThirdPanel = 'done';
    },
    /** end nav */


    // helpers
    makeLocationForm: function(location) {
        var jObj;
        var this_ = this;
        var locString = this.parent.FormMaker.locationToString(location);

        // TODO refactor this one
        if (locString !== undefined) {
            this_.locationVal = location;

            jObj = jQuery('#templates .location_form').clone();
            jObj.find('.loc span').text(locString);

        } else {
            jObj = jQuery('#templates .tweet_form').clone();
            this.parent.FormMaker.makeLocationDiv(jObj.find('input'), this_);
        }

        jQuery('#location').html(jObj);
    },

    _getItem: function(id, name, type, jObj) {
        return {
            id: id,
            name: name ? JUMO.Util.trim(name) : id,
            type: type,
            jObj: jObj
        };
    },

    editLocation: function(div) {
        var jObj = jQuery(div).parent().html('<input placeholder=\"enter your location\" id="m_location" type="text" style=\"width:220px;\" value=""/>');
        this.parent.FormMaker.makeLocationDiv(jObj.find('input'), this);
    },

    // helpers
    _getTags: function(tags, filtername){
        if (tags === undefined) {
            return "";

        } else if ( tags instanceof Array ) {
            return tags.filter(function(tag){ return tag != filtername; }).slice(0,this.tagMax).join(', ');

        } else {
            return tags.context ? tags.context.slice(0,this.tagMax).map(function(tag){ return tag.name; }).join(', ') : "";
        }
    },

    _getOrgImgUrl: function(org){
        if (org.pic_url !== undefined && org.pic_url.length > 0) {
            return org.pic_url;

        } else if (org.img_url !== undefined && org.img_url.length > 0) {
            return org.img_url;

        } else if (org.facebook_id) {
            return 'http://graph.facebook.com/' + org.facebook_id + '/picture?type=large';

        } else if (org.fb_id) {
            return 'http://graph.facebook.com/' + org.fb_id + '/picture?type=large';
        }

        return '/static/img/missing_profile_photo.png';
    },

    saveSurveyResults: function(div, cont) {
        var this_ = this;
        var obj = {};
        var jObj = jQuery(div);

        this.parent.FormMaker.clearError(jObj);

        obj.user = JSON.stringify(this.user);
        JUMO.Util.postJSON('user/update/', obj, function(response) {
                               if (Number(response.error_code) < 1) {
                                   cont();
                               } else {
                                   this_.parent.FormMaker.showError(jObj, 'something went wrong');
                               }
                           });
    },

    getIssueIdsForFollowing: function(following) {
        var issueIds = [];
        var initFollowingOrgIds = this._init_following.map(function(item){ return item.id; });
        var followingOrgIds = following
            .filter(function(item) { return item.type == 'org'; })
            .map(function(item){ return item.id; })
            .filter(function(id){
                        return initFollowingOrgIds.indexOf(id) < 0; });

        this.recommendedIssues.map(function(category){
                                       category.issues.map(function(issue){
                                                               if (issue.id) {
                                                                   issue.orgs.map(function(org){
                                                                                      // test init following orgids incase user has unfollowed an issue related to that org already
                                                                                      if (followingOrgIds.indexOf(org.id) > -1 && issueIds.indexOf(issue.id) < 0){
                                                                                          issueIds.push(issue.id);
                                                                                      }
                                                                                  });
                                                               }
                                                           });
                                   });
        return issueIds;
    },

    followSelectedEntities: function(cont, jObj){
        var this_ = this;

        this.parent.FormMaker.disableSubmit(jObj);

        var orgs = this.following
            .filter(function(item) { 
                        return item.type == 'org'; })
            .map(function(item){ 
                     if (JUMO.Util.isNumeric(item.id)) {
                         return Number(item.id);                          
                     } else {
                         return item.id;         
                     }
                 });

        // handle follow org & then place another request for follow issues
        return JUMO.Util.postJSON('user/action/follow/', {
                                      items: orgs,
                                      item_type: 'org',
                                      user_id: this.user.id,
                                      action: 'follow'
                                  }, function(data) {
                                      if (data.result !== undefined && data.result.result > 0) {
                                          var issues = this_.getIssueIdsForFollowing(this_.following);
                                          this_.trackFunnel('Followed Things', {
                                                               "number issues followed": issues.length,
                                                               "number orgs followed"  : orgs.length
                                                           });
                                          if (issues.length > 0){
                                              return JUMO.Util.postJSON('user/action/follow/', {
                                                                            items: issues,
                                                                            item_type: 'issue',
                                                                            user_id: this_.user.id,
                                                                            action: 'follow'
                                                                        }, function(data) {
                                                                            this_.parent.FormMaker.enableSubmit(jObj);
                                                                            if (data.result !== undefined && data.result.result > 0) {
                                                                                return cont();
                                                                            }
                                                                            return this_.parent.FormMaker.showParsedError(jQuery('.submit_spacer'), data);
                                                                        });
                                          }
                                          this_.parent.FormMaker.enableSubmit(jObj);
                                          return cont();
                                      }
                                      this_.parent.FormMaker.enableSubmit(jObj);
                                      return this_.parent.FormMaker.showParsedError(jQuery('.submit_spacer'), data);
                                  });
    },

    makeFollowingItem: function(item){
        var this_ = this;

        return jQuery('#templates .follow_item').clone()
            .find('.text').text(item.name)
            .end()
            .find(".remove").click(function(event) {
                                       this_.removeFollowing(item);
                                       jQuery(this).parent().slideUp(200);
                                   })
            .end();
    },

    // helpers
    randomiseRecommendedOrgs: function(recommendedIssues){
        recommendedIssues.map(function(issueGroup) {
                                  issueGroup.issues.map(function(issue) {
                                                            issue.orgs = issue.orgs.sort(function() { return 0.5 - Math.random(); });
                                                        });
                              });
        return recommendedIssues;
    },

    setLocationVal: function(val, jObj, doNotAppend) {
        var this_ = this;
        if (!val || val.length < 1){ return; }

        if (!this.panel || Number(this.panel) < 3){
            jObj.parent().find('.loc').remove();
            jObj.after("<div class=\"loc\">" + this.parent.FormMaker.locationToString(val) + "</div>");
            this.getNearbyOrgs(val);

        } else {
            this.getNearbyOrgs(val, function(nearbyorgs){
                                   this_.drawNearbyOrgs(jQuery('#issues .follow_row:last'), nearbyorgs);
                               });
        }

        this.locationVal = val;
    },

    showUserImage: function(jObj, fb_id) {
        if (fb_id !== undefined) {
            var imgURL = "http://graph.facebook.com/" + String(fb_id) + "/picture?type=large";
            jObj.find('.profile_img').attr('src', imgURL).show();
        }
    },
    removeFollowing: function(item){
        item.jObj.removeClass('checked');

        this.following = this.following.filter(function(it) {
                                                   return it.id != item.id;
                                               });

        if ((this.following === undefined || this.following.length < 1)) {
            jQuery('#following').html('<h3>your profile</h3>follow organizations and issues to get started<br /><br />');
        }
    },
    addFollowing: function(item){
        item.jObj.addClass('checked');

        if (this.following.map(function(item){ return item.id; }).indexOf(item.id) < 0) {
            return this.following.push(item);
        }
    },
    isOrgBeingFollowed: function(id) {
        return this.following.map(function(org){ return org.id; }).indexOf(id) < 0 ? false : true;
    },
    getImageForIssue: function(name){
        return "<img src='/static/img/" + (name.split(' ')[0].toLowerCase()) + "_lr.png' ></img>";
    },
    getWhiteImageForIssue: function(name){
        return "<img src='/static/img/" + (name.split(' ')[0].toLowerCase()) + "_white.png' ></img>";
    },
    showError: function(text) {
        jQuery('.submit_spacer .notification').show().text(text);
    },
    hideError: function(){
        jQuery('.submit_spacer .notification').hide().text("");
    },
    freezeDocHeight: function() {
        jQuery('#page-content .form_box').css({ height: jQuery('#page-content .form_box').height() + "px", overflow:'hidden' });
    },
    unFreezeDocHeight: function() {
        jQuery('#page-content .form_box').css({ height: 'auto' });
    }
};