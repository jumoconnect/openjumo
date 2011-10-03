"use strict";
/**
 * Sets up the jumo autocomplete search
 * 
 * 
 * @requires jqueryui
 * @requires jquery
 */

JUMO.Modules.Search = {
    parent: JUMO,
    initialize: function() {
        var this_ = this;
        this.timesSearched = 0;
        this.searchInput = jQuery('#searchbar');
        this.searchForm = jQuery('#searchbar').parent();
        this.termCompleteInput = jQuery('input.termcomplete');
                
        // search
        this.setupSearch(this.searchInput, [], function(val) {
                             this_.parent.Modules.Tracking.trackActionSYNC('Search Found', {
                                                                               query: val.query, 
                                                                               "item found": val.name,
                                                                               "item index": val.index,
                                                                               "times searched": this_.timesSearched
                                                                           }, function() {
                                                                               return window.location = val.url;                                                                   
                                                                           });                                 
                         }, "all_orgtypes");
        
        // setup term completion an any input class'd for it
        if (this.termCompleteInput.length) {
            this.setupTermCompletion(this.termCompleteInput);
        }
        
        if (this.parent.isErrorPage) {
            this.setupSearch(jQuery('#errorsearchbar'), [], function(val){
                                 return window.location = val.url;
                             }, "all_orgtypes");
        }
    },

    setupSearch: function(jObj, items, cont, restrictType) {
        var this_ = this;

        if (!jObj || jObj.length < 1){ return; }
       
        var placeholder = jObj.attr('placeholder');
        jObj
            .val(placeholder)
            .focus(function(){
                       if (jObj.val() == placeholder) {
                           return jObj.val("").removeClass('placeholder');
                       }
                   })
            .focusout(function(){
                          if (jObj.val().length < 1) {
                              jObj.val(placeholder).addClass('placeholder');
                          }
                      })
            .autocomplete({
                              source: function( request, continuation ) {
                                    JUMO.Util.ajaxGet({ url: '/json/v1/search/onebox',
                                                        data: {
                                                                search: request.term,
                                                                restrict_type: restrictType
                                                              },
                                                        success: function(response) {
                                                             this_.timesSearched = this_.timesSearched + 1;
                                                             if (response && response.result) {
                                                                 return continuation(response.result);
                                                             }
                                                             return continuation([]);
                                                        },
                                                        error: function(){ continuation([]); } // override error popup if autocomplete errors
                                                    });
                              },
                              minLength: 2,
                              select: function( event, ui ) {
                                  ui.item.query = jObj.val();
                                  jObj.val( ui.item.name );
                                  cont(ui.item);
                                  return false;
                              }
                          })
            .data( "autocomplete" )._renderItem = function( ul, item ) {
                if (item) {
                    jQuery( "<li class=\"clearfix\"></li>" )
                        .data( "item.autocomplete", item ) 
                        .append(this_.getSearchHtmlForEntity(item))
                        .appendTo( ul );
                    return item;
                }
                return "";
            };

        this.searchForm.submit(function(){
                                   if (jObj.val() == placeholder) {
                                       jObj.val('');
                                   }
                                   return true;
                               });
    },

    getHRTypeForType: function(type) {
        if (type == 'user') {
            return 'person';
        } else if (type == 'org') {
            return 'project';
        } else {
            return type;
        }
    },

    getSearchHtmlForEntity: function(item) {
        var img = item.image_url ? "<img src='" + item.image_url + "' />" : "";
        var iefix = this.browserIsIE ? "div" : "span";  // no idea why IE works if I put a DIV in an A tag
        var iefix2 = this.browserIsIE ? "" : "</span>"; // no idea why IE works if I _DONT_ close the DIV in the A tag 
        return "<a>" + img +
            "<" + iefix +" class=\"result_container\">" +
            "<span class=\"name\">" + item.name + "</span>" +
            "<span class=\"followers\">" + item.num_followers + " people follow this <b>" + this.getHRTypeForType(item.type) + "</b></span>" +
            iefix2 + "</a>";
    },
    
    setupTermCompletion: function(target) {
        var cache = {}; // results cache
        var lastxhr; // ref to last outgoing req incase resp order gets all f'd
        target
            .autocomplete({
                              source: function( req, callback ) {
                                  if (cache[req.term]) {
                                      return callback( cache[req.term] );
                                  } else {
                                      lastxhr = JUMO.Util.ajaxGet({ url: '/json/v1/autocomplete',
                                                                    data: { q: req.term },
                                                                    success: function(response, status, xhr) {
                                                                        cache[req.term] = response['result'];
                                                                        if (xhr === lastxhr) {
                                                                            if (response && response['result']) {
                                                                                return callback( response['result'] );
                                                                            }
                                                                        }
                                                                        return callback([]);
                                                                    },
                                                                    error: function(){ /*callback([]);*/ } // override error popup if autocomplete errors
                                                                  });
                                  }
                              },
                              select: function(e, ui) {
                                        // track metrics event
                                        JUMO.Modules.Tracking
                                            .trackActionSYNC('Autocomplete Select', {
                                                                               query: target.val(), // send what's in the searchbox
                                                                               "item found": ui.item.label,
                                                                               "item index": ui.item.index
                                                                           });
                                        // replace what's in the searchbox w/ autocomplete value
                                        target.val( ui.item.label );
                                        return false;
                              },
                              minLength: 2
                          })
            .data( "autocomplete" )._renderItem = function( ul, item ) {
                    // NOTE: since autocomplete results don't return index, when rendering, 
                    // add index property to reference when sending metrics event
                    item.index = ul.children('li').length;
                    return jQuery( "<li></li>" )
                        .data( "item.autocomplete", item ) // returned as "ui" in the select item
                        .append( "<a>" + item.label + "</a>" )
                        .appendTo( ul );
                };
    }
};