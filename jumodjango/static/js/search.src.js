"use strict";
/** 
 * this is the javascript page for the search results page
 * 
 * it is only used by that page
 */

JUMO.SearchResults = {
    parent:JUMO,
    limit:20,
    currentQuery: undefined,
    currentType: undefined,
    currentLocation: undefined,
    currentOffset: 0,
    initialize: function() {
        this.searchBox = jQuery("#search_box");
        this.searchButton = jQuery("#search_button");
        this.leftSide = jQuery('#facets');
        this.searchResults = jQuery('.search_results');
        this.locationFilters = jQuery('#location_filters a');
        this.nearMe = jQuery('#near_me');
        this.moreResults = jQuery('#more_results');
        this.pageHeading = jQuery('h1');
        this.relatedSearches =jQuery('.related_search_queries');
        this.currentQuery = this.parent.Util.getUrlParameterByName('q');
        this.setupEvts();
        
        if(JUMO.browserIsIE) {
            var val = this.searchBox.val() || this.searchBox.text();
            if (val && val.length > 0) {
                return;
            } else {
                JUMO.Util.initPlaceholder(this.searchBox);
                this.searchBox.bind('focus blur', function(evt) {
                              JUMO.Util.fixPlaceHolder(jQuery(evt.target), evt.type);
                          });
            }
        }
    },

    setupEvts: function() {
        var this_ = this;

        this.searchButton.click(function(evt) {
                                    evt.preventDefault();
                                    // since we're preventing default to avoid page reload, need to set focus on button
                                    // this also allows autocomplete to know it is no longer focused on not open
                                    $(this).focus();
                                    this_.submitSearch({ query:this_.searchBox.val() });
                                });   

        this.locationFilters.click(function(evt){
                                       evt.preventDefault();
                                       var jObj = jQuery(this);
                                       var loc = jObj.attr('data-val');

                                       jQuery('#location_filters a').removeClass('selected');
                                       jObj.addClass('selected');
                                       
                                       this_.submitSearch({location: loc}); 
                                   });


        this.leftSide.find('.filter').live('click', function() {                          
                                               var jObj = jQuery(this);
                                               var nameDiv = jObj.find('span.name');
                                               var type = nameDiv.attr('data-type');
                                               var humanType = nameDiv.text();
                                               
                                               this_.submitSearch({ 
                                                                      query: this_.currentQuery, 
                                                                      type: type, 
                                                                      doNotRebuildFacets: true 
                                                                  }); 
                                               this_.leftSide.find('.filter').removeClass('selected');
                                               jObj.addClass('selected');
                                               this_.pageHeading.text(humanType);
                                           });
        
        this.moreResults.click(function(evt) {                                        
                                   this_.submitSearch({
                                                          query: this_.currentQuery,
                                                          doNotRebuildSearchItems: true,
                                                          offset: this_.currentOffset + this_.limit
                                                      });
                               });
    },

    /**
     * doin it the 'params' way allows us to easily add params and
     * to be able to call this function w/o knowing order of args
     * 
     * @param query
     * @param type
     * @param doNotRebuildFacets
     * @param location
     * @param doNotRebuildSearchItems
     * @param offset
     */
    submitSearch: function(params) { 
        var this_ = this;

        // if no val is passed in, use previous
        this.currentQuery = params.query || this.currentQuery;
        this.currentType = params.type || this.currentType;
        this.currentLocation = params.location || this.currentLocation;
        this.currentOffset = params.offset || 0;

        var data = {
            q: this.currentQuery, 
            format: 'html', 
            type: this.currentType,
            location: this.currentLocation,
            lat: this.userLocation ? this.userLocation.lat : undefined,
            lng: this.userLocation ? this.userLocation.lng : undefined,
            limit: this.limit,
            offset: this.currentOffset
        };
        
        JUMO.Util.ajaxGet({ url: '/json/v1/search',
                            data: data,
                            success: function(data) {
                                if (data && data.result) {
                                    if (!params.doNotRebuildFacets) {                                    
                                        this_.leftSide.html(data.result.facets);                                   
                                    }                                
                                    
                                    if (!params.doNotRebuildSearchItems) {
                                        this_.searchResults.html(data.result.items);                                        
                                    } else {
                                        this_.searchResults.find('li').last().removeClass('last');
                                        var searchResultsHTML = jQuery(data.result.items);
                                        searchResultsHTML.filter('li').first().removeClass('first');
                                        this_.searchResults.append(searchResultsHTML);
                                    }
                                    
                                    this_.moreResults.html(data.result.more_results);
                                    
                                    this_.relatedSearches.html(data.result.related);
                                    
                                    if (data.result.nearMe) {
                                        this_.nearMe.html(data.result.nearMe);
                                    }
                                } else {
                                    //console.log('no results');
                                }
                            }
                          });
        
        if (!this.userLocation) {
            this.updateNearMe(data);             
        }
    },
    
    setUserLocation:function(lat,lng){
        this.userLocation = {
            lat: lat,
            lng: lng
        };
    },

    getUserLocation: function(cont) {
        var this_ = this;

        if (this.userLocation) {
            cont(this.userLocation.lat, this.userLocation.lng);

            // Try W3C Geolocation (Preferred)
        } else if(navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                                                         this_.setUserLocation(position.coords.latitude, position.coords.longitude);
                                                         cont(position.coords.latitude, position.coords.longitude);
                                                     }, function() {
                                                         // no location
                                                         cont(undefined, undefined);
                                                     });
            // Try Google Gears Geolocation
        } else if (window.google && google.gears) {
            var geo = google.gears.factory.create('beta.geolocation');
            geo.getCurrentPosition(function(position) {
                                       this_.setUserLocation(position.latitude, position.longitude);
                                       cont(position.latitude, position.longitude);
                                   }, function() {
                                       // no location
                                       cont(undefined, undefined);
                                   });

            // Browser doesn't support Geolocation
        } else {
            // no location
            cont(undefined, undefined);
        }
    },

    updateNearMe: function(data) {
        var this_ = this;

        this.getUserLocation(function(lat,lng) {
                                 data.lat = lat;
                                 data.lng = lng;
                                 JUMO.Util.ajaxGet({
                                                       url: '/json/v1/search',
                                                       data: data,
                                                       success: function(data) {
                                                           if (data !== undefined && data.result !== undefined && data.result.nearMe !== undefined) {
                                                               this_.nearMe.html(data.result.nearMe);
                                                           } else {
                                                               //console.log('no results');
                                                           }
                                                       }
                                                   });
                             });
    }
};