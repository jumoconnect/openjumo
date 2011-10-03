/**
 *
 * Initializes org verify forms
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

JUMO.Verify = {
    initialize: function(id) {
        this.id = id; // id for entity we are 'managing'
        this.manageType = 'org';
    },

    setLocationVal: function(val, jObj) {
        jObj.parent().find('.loc').remove();
        jObj.after("<div class=\"loc\">" + FormMaker.locationToString(val) + "</val>");
        this.locationVal = val;
    }
};
