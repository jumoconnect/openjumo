"use strict";
/**
 * Sets up the jumo discovery module
 * see templates/util/discover.html
 * 
 * the discovery module has categories -> sub categories -> orgs.
 * this file allows users to find orgs by filtering using categories and subcategories
 * 
 * @requires jquery
 */

JUMO.CategoryDiscover = {
    parent: JUMO,
    initialize: function() {
        this.jObj = jQuery('#discover_module');
        if (!this.jObj && this.jObj.length < 1) { return; } 
        else {
            this.setupMouseEvents();            
        }
    },
    
    showOrgsForChild: function(child) {
        this.jObj.find('.discovery_item_group').hide();
        return this.jObj.find('.discovery_item_group.' + child).show();        
    },

    showSubcategoriesForChild: function(child) {
        var subCat = this.jObj
            .find('.sub_category_group').hide().end()
            .find('.sub_category_group.' + child).show();

        var orgChild = subCat.find('.tab.selected').attr('data-child');

        this.showOrgsForChild(orgChild);
        return subCat;
    },
    
    selectJobj: function(jObj){
        jObj.parent()
            .find('.tab')
            .removeClass('selected').end().end()
            .addClass('selected');         
    },

    setupMouseEvents: function() {
        var this_ = this;

        // top categories        
        this.jObj.find('.top_categories .tab').live('click', function() {
                                                        var jObj = jQuery(this);
                                                        var child = jObj.attr('data-child');
                                                        this_.showSubcategoriesForChild(child);
                                                        
                                                        this_.selectJobj(jObj);
                                               });


        // sub categories
        this.jObj.find('.sub_categories .tab').live('click', function() {
                                                        var jObj = jQuery(this);
                                                        var child = jObj.attr('data-child');
                                                        
                                                        this_.selectJobj(jObj);
                                                        this_.showOrgsForChild(child);
                                                    });
    }
};

jQuery(document).ready(function(){
                           JUMO.CategoryDiscover.initialize();
});