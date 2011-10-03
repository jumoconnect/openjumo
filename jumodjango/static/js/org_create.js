/**
 *
 * Initializes org create forms
 *
 * @requires jquery
 * @requires base.js
 * @requires forms.js
 *
 * @param form
 *  outer most is the pages or sections
 *  inner is each item and its type
 *  types include section, name, number, select
 */

var OrgCreate = {
    parent: JUMO,
    maxVisionStatementLength: 250,
    speed: 100,
    panel: 1,
    specialTypes: [],
    initialize: function(form, def) {
        this.type = JUMO.Util.getHash() || def;       
        this.setupMouseEvts();
    },

    setupMouseEvts: function() {
        var this_ = this;
        var saveBtn = jQuery('#save');

        saveBtn.click(function() {                                   
                                  if (this_.panel == 1) {
                                      this_.createNewOrg(saveBtn, 
                                                         function(jObj, response) { 
                                                             if (response && response.result) {
                                                                 this_.panel = this_.panel + 1;
                                                                 jQuery('#step li:eq(0)').addClass('checked');
                                                                 
                                                                 this_._gotoSecondPanel(jObj, response.result);                                                                                                                                      
                                                             } else {
                                                                 Checker.showParsedError(jObj, response);
                                                             }                                                                 
                                                         });
                                  } else {
                                      this_.saveOrgInfo(saveBtn,
                                                        function() {   
                                                            window.location = "/org/manage/" + this_.org.id + "?new_user=true";                                                            
                                                        });                                          
                                  }
                              });
        
        jQuery('input[type="text"], textarea', jQuery('body')).live('focus blur', function(evt) {
                                                                this_.parent.Util.fixPlaceHolder(jQuery(this), evt.type);
                                                            });
        jQuery('#counter').hide();
        this.parent.Util.makeCharCountDiv(jQuery('#vision_statement'), jQuery('#counter'), this.maxVisionStatementLength);

        jQuery('#counter').text(this.maxVisionStatementLength);

        jQuery(':checked').attr('checked', false);
        
        jQuery("input[name='social_mission']").change(function() {                                                          
                                                          if (jQuery(this).val() == 'no') {
                                                              jQuery('#social_error').show();
                                                              jQuery('#save').addClass('disabled');
                                                              
                                                          } else {
                                                              jQuery('#social_error').hide();
                                                              jQuery('#save').removeClass('disabled');
                                                          }
                                                      });                        
    },
    /** end mouse events */
    
    /** helper for going to second panel from 1st panel */
    _gotoSecondPanel: function(jObj, org) {  
        this.org = JSON.parse(org);
        jObj.html('next &#187;');

        this.gotoSecondPanel(function() { jQuery('#step li:eq(1)').addClass('filled');});
    },

    gotoSecondPanel: function(cont) {
        var this_ = this;

        this.panel = 2;
        this.freezeDocHeight();
        cont();

        this.forms = this.buildTagForms();

        // correct width 
        jQuery('#tags .sortable_cont').css({width: '99%'});

        jQuery('.notification').hide().html('');
        
        jQuery('#first_panel').animate({width: 'hide'}, 
                                       this.speed, 
                                       function() {
                                           jQuery('#second_panel').animate({width: 'show'}, this_.speed, function() {
                                                                               jQuery(window).scrollTop(0);
                                                                               this_.unFreezeDocHeight();
                                                                           });
                                       });
    },

    buildTagForms: function() {
        var tagForms = {tags:[{
                                  id: 'working_locations',
                                  name: 'Working In',
                                  type: 'multi_location',
                                  required: false,
                                  val:[],
                                  help: "Please enter the cities or countries in which you work. List in order of importance."
                              },{
                                  id: 'context',
                                  name: 'Working On',
                                  type: 'dependent_select',
                                  required: false,
                                  sub: 'tags',
                                  val:[],
                                  help: 'Please choose up to six tags from the issue areas below. List in order of importance.'
                              }]
                       };
        
        return FormMaker.buildForms(['tags'], tagForms, jQuery('#tag_forms'));
    },

    // we can safely assume that an org has been created at this time            
    saveOrgInfo: function(jObj, cont) {
        var this_ = this;
        var fbid = jQuery('input[name="facebook_url"]').val();        
        var formObj = Checker.validateFormModules(this.org.id, this.forms);

        this.org.tags = {};
        this.org.tags.geo = formObj.tags.geo;        
        this.org.tags.context = formObj.tags.context;
        this.org.working_locations = formObj.working_locations;
        this.org.twitter_id = FormUtils.normalizeTwitterId(jQuery('input[name="twitter_username"]').val());

        // remove defaults for fbid and twitter        
        if (FormUtils.normalizeTwitterId(jQuery('input[name="twitter_username"]').attr('placeholder')) == this.org.twitter_id) { this.org.twitter_id = ""; }
        if (jQuery('input[name="facebook_url"]').attr('placeholder') == fbid){ fbid = ""; }

        
        // these properties are not editable on the db...and have to be deleted
        delete this.org.admin;
        delete this.org.admins;
        delete this.org.org_type;
        delete this.org.date_created;
        delete this.org.date_updated;            
        
        // parse twitter id and fbid
        jObj.addClass('disabled');
        jObj.after('<img class=\"submit_loading_img\" src="/static/img/ajax-loader.gif" />');
        
        if (fbid) {
            this.getParsedFBId({ fbid: fbid },
                               function(result) {  
                                   this_.org.facebook_id = result.facebook_id || "";
                                   this_.postUpdate(this_.org, jObj, cont);
                               }, jObj);
        } else {
            this.postUpdate(this.org, jObj, cont);
        }
    },
    
    getParsedFBId: function(obj, cont, jObj) {
        var this_ = this;
        
        jObj.parent().find('.notification').html('');
        this.parent.Util.postJSON('org/normalize_facebook_id/', obj, function(response) {
                               if (response && response.result) {
                                   cont(response.result);
                               } else {
                                   jObj.removeClass('disabled');
                                   JUMO.Util.removeLoadingImg(jObj); 
                                   
                                   Checker.showParsedError(jObj, response);                              
                               }}, false, function(response) {
                                   jObj.removeClass('disabled');
                                   this_.parent.Util.removeLoadingImg(jObj);                                
                                   this_.parent.Modules.Popup.showErrorPopup(this_.parent.Util.getParsedErrorText(response));
                          });
    },
    
    _handleResponse: function(jObj, cont, response) {
        jObj.removeClass('disabled');
        this.parent.Util.removeLoadingImg(jObj); 
        
        if (response && response.result) {
            cont(jObj, response);
        } else {
            Checker.showParsedError(jObj, response);
        }
    },

    postUpdate: function(leDude, jObj, cont) {
        var this_ = this;
        jObj.addClass('disabled');        
        this.parent.Util.addLoadingImg(jObj); 
        
        var obj = {};
        obj['org'] = JSON.stringify(leDude);
        
        this.parent.Util.postJSON('org/update/', obj, function(response) {
                               this_._handleResponse(jObj, cont, response);
                           });
   },
    
    postSave: function(obj, jObj, cont) {
        var this_ = this;
        jObj.addClass('disabled');
        this.parent.Util.addLoadingImg(jObj); 
        
        this.parent.Util.postJSON('org/create/', obj, function(response) {
                          jObj.removeClass('disabled');
                          this.parent.Util.removeLoadingImg(jObj);                          
                          this_._handleResponse(jObj, cont, response);
                     }, false, function(response) {
                               jObj.removeClass('disabled');
                               this_.parent.Util.removeLoadingImg(jObj);                                
                               this_.parent.Modules.Popup.showErrorPopup(this_.parent.Util.getParsedErrorText(response));
                           });
    },

    /**  
     * @returns 
     * {org: {}, error_text: ""}
     */
    validateCreateNewOrg: function() {
        var error_text = "";
        var org = {};
        var vision_placeholder = "In one sentence describe this organization's vision.";
        var profit_radio = jQuery("input[name='profit']:checked").val();
        
        org['name'] = jQuery("input[name='organization_name']").val();
        org['vision_statement'] = jQuery("textarea[name='vision_statement']").val();
        org['profit'] = "";
        org['social_mission'] = jQuery("input[name='social_mission']:checked").val();
        org['admin'] = jQuery("input[name='admin']:checked").val();
        
        // check org name
        if (!org['name'] || org['name'].length < 1) {
            error_text = error_text + ' Organization Name cannot be blank.<br />';
        }
        
        // check vision statement
        if (!org['vision_statement'] || org['vision_statement'].length < 1 || org['vision_statement'] == vision_placeholder){
            error_text = error_text + ' Please enter a Vision Statement. <br />';
        } else if (org['vision_statement'].length > this.maxVisionStatementLength) {
            error_text = error_text + ' Your Vision Statement must be less than 250 characters. <br />';
        }

        // check social mission
        if (!org['social_mission']) {
            error_text = error_text + ' Please select whether you seek to achieve a social or environmental mission. <br />';
        }

        // --- validating profit is weird ---
        if (!profit_radio) {
            error_text = error_text + ' Please select a type of mission driven organization. <br />';

        } else if (profit_radio == 'for-profit') {
            org['profit'] = "yes";

        } else if (profit_radio == 'other') {
            org['profit'] = "yes";
        }

        // validate admin
        if (!org['admin']) {
            error_text = error_text + ' Please select whether you want to be admin or not. <br />';
        }

        return {
            org:org, 
            error_text:error_text
        };  
    },

    createNewOrg: function(jObj, cont){
        if (jObj.hasClass('disabled')) { return; }
        
        var org_form =  this.validateCreateNewOrg();
        
        if (org_form.error_text == '') {
            this.postSave(org_form.org, jObj, cont);

        } else {
            jQuery('.notification').html(org_form.error_text).show();
        }                         
    }
};