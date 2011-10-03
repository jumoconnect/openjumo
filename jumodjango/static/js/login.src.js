/**
 *
 * Initializes Login, ForgotPW and ResetPW
 *
 * @requires jquery
 * @requires base.js
 * @requires forms.js
 *
 * @see extended permissions docs: http://developers.facebook.com/docs/authentication/permissions
 * this is what gets passed as 'perms' in FB.login
 *
 * @see graph api docs: http://developers.facebook.com/docs/api
 * used in the FB.api('/me*...
 *
 * compile script: java -jar compiler.jar --js=login.src.js --js_output_file=login.js
 */

var Login = {
    parent:JUMO,
    initialize: function(params, type ) {
        jQuery('#id_username').focus();
        this.setupLogin(params.email_id, params.pw_id, params.login_submit);            
    },

    setupLogin: function(email_id, pw_id, loginSubmitBtn){
        var this_  = this;
        jQuery(email_id + ", " + pw_id).keyup(function(e) {
                                                  if (e.keyCode == 13) {
                                                      jQuery('#login_form').submit();
                                                  };
                                              });
    },

    /**
     * UTILS
     */
    _showSubmitError: function(jObj, submitDiv, text) {
        Checker.enableSubmit(submitDiv);
        JUMO.Util.removeLoadingImg(jObj);

        if (text !== undefined) {
            Checker.showError(submitDiv, 'your username and password are incorrect');
        }
    },
    showSignupForm: function() {
        jQuery('#areyousignedin').hide();
        jQuery('#create_account_button').slideUp(350);
        jQuery('#create_account_form').slideDown(350);
    }
};
