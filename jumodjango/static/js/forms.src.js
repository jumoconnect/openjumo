"use strict";
/**
 *
 * this module takes a blob of json and builds forms for those items
 * JSON -> Creator which returns a val function and the jquery object for that form
 * the val function calls client side validation and returns error text to be used by the jquery object AND returns 'ERROR'
 *
 * @author Brennan Moore brennan@jumo.com
 * @requires jquery
 * @requires base.js
 * 
 * compile script: java -jar compiler.jar --js=forms.src.js --js_output_file=forms.js
 */

/**
 * takes json and creates html forms that validate themselves on .val()
 *
 * @requires div #form
 * @requires templates/util/form_templates.html
 * 
 * @param formTypes array of names for each tab of the form
 * @param form object keyed by type JSON for each form
 *
 * @param module A form object containing a val function and a jquery object referencen to that form
 * 
 * @note if there is only one formType it will not display tabs
 * 
 */
JUMO.FormMaker = {
    clearDefault:function(element, defaultValue) {
        if (jQuery(element).val() == defaultValue) {
            jQuery(element).val('');
            jQuery(element).removeClass('placeholder');
        }
    },

    restoreDefault: function(element, defaultValue) {
        if (!jQuery(element).val() || jQuery(element).val() === '') {
            jQuery(element).val(defaultValue);
            jQuery(element).addClass('placeholder');
        }
    },

    getInputs: function(formID) {
        return jQuery('#' + formID + ' input');
    },

    checkAll: function() {
        jQuery('input:checkbox').each(function() {
                                          jQuery(this).attr('checked', true);
                                      });
    },

    uncheckAll: function() {
        jQuery('input:checkbox').each(function() {
                                          jQuery(this).attr('checked', false);
                                      });
    },

    attachFormDefaults: function() {
        var this_ = this;
        var inputs = jQuery('input, textarea');
        inputs.each(function(i, el) {
                        jQuery(this).focus(function() {
                                               this_.clearDefault(jQuery(this), jQuery(this).attr('placeholder'));
                                           });
                        jQuery(this).blur(function() {
                                              this_.restoreDefault(jQuery(this), jQuery(this).attr('placeholder'));
                                          });
                        this_.restoreDefault(this);
                    });
    },

    /**
     * returns a location object of some sort
     */
    getLocationForString: function(str, cont, errorcont) {
        this.Placemaker.getPlaces(str, function(resp) {
                                      if (resp) {
                                          if (!JUMO.Util.isArrayLike(resp)) {
                                              resp = [resp];
                                          }
                                          cont(resp
                                               .filter(function(location){ return location.placeTypeName && location.placeTypeName.content == 'State' ? false : true; })
                                               .map(function(location) {
                                                        // NOT USED: 'continent', 'country',
                                                        var possibleNames = ['locality1', 'locality2', 'admin1', 'admin2', 'admin3', 'country', 'town', 'suburb'];
                                                        var postal = location.uzip || (location.postal ? location.postal.content : undefined) || "";
                                                        
                                                        var loc = {
                                                            name: location.name ? location.name : "",
                                                            latitude: location.centroid ? location.centroid.latitude : "",
                                                            longitude: location.centroid ? location.centroid.longitude : "",
                                                            'postal_code': postal,
                                                            address: location.line1 ? location.line1 : "",
                                                            type: location.placeTypeName && location.placeTypeName.content ? location.placeTypeName.content : "",
                                                            raw_geodata: location
                                                        };
                                                        
                                                        possibleNames
                                                            .filter(function(name){ return location[name] ? true : false; })
                                                            .map(function(name){
                                                                     var type = location[name].type;
                                                                     if (type == 'Country') {
                                                                         loc['country_name'] = location[name].content;
                                                                     } else if (type == 'State' || type == 'County' && location[name].content == 'Brooklyn') { // no idea how to generalize this
                                                                         loc.region = location[name].content;
                                                                     } else if (type == 'Local Administrative Area' || type == 'Town') {
                                                                         loc.locality = location[name].content;
                                                                     }
                                                                 });
                                                        return loc;
                                                    })
                                              );
                                      }
                                  }, errorcont);
    },
    
    /**
     * make location div
     * @param parent requires a setLocationVal method
     */
    makeLocationDiv: function(jObj, parent, cont) {
        var this_ = this;
        cont = cont || function(val){ return parent.setLocationVal(val, jObj); };
        
        jObj.autocomplete({
		                      source: function( request, response ) {
                                  // reset data div
                                  JUMO.FormMaker.MultiLocationForm.setVal(jObj.parent(), '');
                                  this_.getLocationForString(request.term,
                                                             function(locations){
                                                                 this_.clearError(jObj);
                                                                 response(locations);
                                                             },
                                                             function(v){ 
                                                                 // todo -- make this display a no results found thing
                                                                 response([]);
                                                             });
			                  },
			                  minLength: 2,
	                          focus: function( event, ui ) {
				                  jObj.val(this_.locationToString(ui.item));
                                  return false;
	                          },
                              open: function() {
				                  jQuery(this).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" );
			                  },
			                  close: function() {
				                  jQuery(this).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" );
			                  },
			                  select: function( event, ui ) {
                                  this_.clearError(jObj);
				                  jObj.val(this_.locationToString(ui.item));
                                  cont(ui.item);
				                  return false;
			                  }
                          }).data( "autocomplete" )._renderItem = function( ul, item ) {
			                  jQuery( "<li></li>" )
				                  .data( "item.autocomplete", item )
				                  .append("<a>" + this_.locationToString(item) + "</a>")
				                  .appendTo( ul );
                              return item;
		                  };
    },

    locationToString: function(location){
        var result = "";

        if (!location)  { return ""; }

        var raw_geodata;
        try {
            if (JSON && JSON.parse && location.raw_geodata){
                raw_geodata = JSON.parse(location.raw_geodata);
            }            
        } catch (x) {
            // ie7 fails due to 'syntax error'
        }

        if (location.name && location.name != location.locality) {
            result += location.name + " ";

        } else if (raw_geodata && raw_geodata.name && raw_geodata.name != location.locality && raw_geodata.name != location.region && raw_geodata.name != location.country_name) {
            result += raw_geodata.name + " ";

        } else if (location.locality) {
            result += location.locality + ", ";
        }
        
        if (location.region && location.region != location.name) {
            result += location.region + " ";
        } 

        if (location.country_name && location.country_name != location.name) {
            result += location.country_name;
        } 
        
        if (location.type) {
            result += " (" + location.type + ")";
        }
        
        return JUMO.Util.trim(result);
    },

    // helpers
    highlightDiv: function(jObj) {
        return jObj.addClass('highlight');
    },
    unHighlightDiv: function(jObj) {
        return jObj.removeClass('highlight');
    },
    findNotificationDiv: function(jObj) {
        var noteObj = jObj.parent().parent().find('.notification');
        return noteObj.length > 0 ? noteObj : jQuery(jQuery.find('.submit_spacer .notification'));
    },
    hideNotificationDiv: function(jObj) {
        return this.findNotificationDiv(jObj).slideUp(100).html('');
    },

    showError: function(jObj, text, type) {
        this.highlightDiv(jObj);
        this.errorType = type;

        return this.findNotificationDiv(jObj).slideDown(50).append(text + "<br />");
    },
    
    showParsedError: function(jObj, response) {
        var text = JUMO.Util.getParsedErrorText(response);
        this.highlightDiv(jObj);

        return this.findNotificationDiv(jObj).slideDown(50).append(text + "<br />");
    },

    clearError: function(jObj) {
        this.errorType = undefined;
        return this.findNotificationDiv(jObj).html('').hide();
    },

    disableSubmit: function(jObj) {
        jObj.addClass('disabled');
    },

    enableSubmit: function(jObj) {        
        jObj.removeClass('disabled');

        // potentially/
        jQuery('.button.disabled').removeClass('disabled');
    }
};


/**
 *
 * Util functions for forms.js
 * mostly contains generators for the custom form types we use
 * this is compiled with forms.js and does not need to be loaded separately
 *
 * + util functions for forms
 *
 * @function val used to get val out of the dom elements / objects
 *
 * @includes Validator, Placemaker (yahooapi), OrderedList - maker, Accomplshment - maker, FormUtils
 */

JUMO.FormMaker.MultiLocationForm = {
    parent: JUMO,
    initialize: function(jObj){
        this.jObj = jObj;

        this.initializeLocationDivs();
        this.setupMouseEvent();
    },

    initializeLocationDivs: function(){
        var this_ = this;
                
        this.jObj.find('.location_input').each(function(index, item) {   
                                                   var jObj = jQuery(item);
                                                   this_.parent.FormMaker.makeLocationDiv(jObj,
                                                                                          this_,
                                                                                          function(val) {
                                                                                              this_.setVal(jObj.parent(), val); });                                         
                                               });
        
    },

    setupMouseEvent: function() {
        var this_ = this;
        this.makeRemove();
        this.setupMakeNewRow();
    },

    makeRemove: function() {
        this.jObj.find(".remove").live('click', function(e) {
                                           e.preventDefault();
                                           jQuery(this).parent().slideUp('slow', function(){ jQuery(this).remove(); });
                                       });
    },

    setupMakeNewRow: function() {
        var this_ = this;
        this.jObj.find('.add').click(function() { 
                                         var item = this_.jObj.find('.empty-item').clone();
                                         item.removeClass('empty-item');
                                         this_.jObj.find('.add').parent().before(item);
                                         
                                         this_.parent.FormMaker.makeLocationDiv(item.find('.location_input'),
                                                                                this_,
                                                                                function(val){
                                                                                    this_.setVal(item, val); });                                         
                                     });
    },

    makeSortable: function() {
        var options = { handle: '' };
        return this.jObj.sortable(options);
    },
    
    setVal: function(jObj, val) {
        if (val) {
            jObj.find('.location_data').val(JSON.stringify(val));            
        } else {
            jObj.find('.location_data').val('');
        }

    },
    
    getVal: function(jObj) {
        return JSON.parse(jObj.parent().find('.location_data').val());
    }
};


/**
 * UTIL
 * interface for Yahoo geo places api
 */

JUMO.FormMaker.Placemaker = {
    config: { appID: 'Rl9xiX7a' },

    /**
     *
     * @param text string search query
     */
    getPlaces: function(text,cont,errorcont){
        this.cont = cont;
        this.errorcont = errorcont;

        var query ='select * from geo.places where text="' + text.replace(",", "") + '" | sort(field="areaRank", descending="true")';
        var url = 'http://query.yahooapis.com/v1/public/yql?q=' + encodeURIComponent(query) + '&format=json&callback=JUMO.FormMaker.Placemaker.retrieve&appid=' + this.config.appID;

        var s = document.createElement('script');
        s.setAttribute('src',url);
        document.getElementsByTagName('head')[0].appendChild(s);
    },
    retrieve: function(resp){
        if (resp !== undefined && resp.query !== undefined && resp.query.count > 0) {
            return this.cont(resp.query.results.place);
        }
        return this.errorcont('location fail');
    }
};
