"use strict";
/**
 *
 * Initializes the donate page for both orgs and campaigs
 *
 * @requires jquery
 * @requires base.js
 *
 * compile script: java -jar compiler.jar --js=donate.src.js --js_output_file=donate.js
 */

var Donate = {
    speed: 200,
    jumoPercent: 15,
    initialize: function(){
        this.jumoDonationDiv = jQuery('#id_jumo_amount');
        this.donationDiv = jQuery('#id_donation_amount');
        this.totalDiv = jQuery('#total_display');
        this.jumoPercentDisplay = jQuery('#jumo_percent_display a');
        this.rewardsList = jQuery('.right_side .rewards li');
        this.errorDiv = jQuery('#errors');
        this.rewards = jQuery('.rewards').length;


        this.donationDiv.focus();
        
        this.setupMouseEvts();

        if (!jQuery('.errorlist').length) {
            this.updateJumoAmount();            
        }

        this.changeDonationAmount(this.getDonationAmount(), false, true);
    },

    setupMouseEvts: function(){
        var this_ = this;
        jQuery("#submit_donation").click(function(){ return this_.donate(jQuery(this)); });
        
        this.setupSuggestedAmounts();
        this.setupRewards();
        this.setupJumoPercent();
        this.setupInputEditing();
    },

    setupSuggestedAmounts: function(){
        var this_ = this;
        
        jQuery('.right_side ul.rewards_list li').click(function() {
                                                           var val = jQuery(this).attr('data-val');
                                                           this_.changeDonationAmount(val);
                                                       });
    },

    changeVal: function(){
        var jObj = jQuery(this);
        var val = this_.inputToNumber(jObj.val(),jObj);
    },

    setupInputEditing: function(){
        var this_ = this;
        var isCalcing = false;

        var update = function(jObj, evt) {
            var keycode = evt.which;
            if (keycode == 39 || keycode == 37 || keycode == 190){ return; }

            //  up
            if (keycode == 38) {
                if (jObj.attr('id') == 'id_donation_amount') {
                    this_.setDonationInputVal(this_.getDonationAmount() + 1);
                    this_.updateJumoAmount();
                } else {
                    this_.setJumoInputVal(this_.getJumoAmount() + 1);
                }
                this_.updateTotal();
                return;
            }

            // down
            if (keycode == 40) {
                if (jObj.attr('id') == 'id_donation_amount') {
                    this_.setDonationInputVal(this_.getDonationAmount() - 1);
                    this_.updateJumoAmount();
                } else {
                    this_.setJumoInputVal(this_.getJumoAmount() - 1);
                }
                this_.updateTotal();
                return;
            }

            // restrict to numbers + .
            // jObj.val(jObj.val().replace(/[^0-9\.]/g,''));

            if (jObj.attr('id') == 'id_donation_amount') {
                this_.updateJumoAmount();
            }
            
            
            this_.setJumoAmount(this_.getJumoAmount());
            this_.setDonationAmount(this_.getDonationAmount());
            this_.updateTotal();
        };

        this.donationDiv.keyup(function(evt) {
                                   return update(jQuery(this), evt);
                               });        

        this.jumoDonationDiv.keyup(function(evt) {
                                       return update(jQuery(this), evt);
                                   });        

    },

    setupRewards: function(){
        var this_ = this;
        
        this.rewardsList.click(function() {
                                   var jObj = jQuery(this);                              
                                   var val = jObj.attr('data-val');

                                   jObj.find('input').attr('checked', 'checked');

                                   this_.rewardsList.removeClass('selected');
                                   jObj.addClass('selected');

                                   this_.setReward(jObj);
                                   
                                   var selectedReward = jQuery('.rewards .selected');
                                   var minAmount = selectedReward.attr('data-val');
                                   var donationAmount = this_.getDonationAmount();
                                  
                                   if (val && val > donationAmount) {
                                       this_.changeDonationAmount(val, jObj);                                       
                                   }
                               });
        
        jQuery('.right_side .rewards li input').click(function() {
                                                          var jObj = jQuery(this);
                                                          var selectedReward = jObj.parent().parent();
                                                          var val = selectedReward.attr('data-val');

                                                          this_.rewardsList.removeClass('selected');
                                                          jObj.addClass('selected');      
                                                          
                                                          this_.setReward(selectedReward);

                                                          if (val) {             
                                                              this_.changeDonationAmount(val, selectedReward);
                                                          }
                                                      });
    },
    
    setupJumoPercent: function() {
        var this_ = this;
        this.jumoPercentDisplay.click(function() {
                                          var jObj = jQuery(this);
                                          
                                          this_.jumoPercentDisplay.removeClass('selected');
                                          jObj.addClass('selected');

                                          this_.jumoPercent = Number((jObj).attr('data-val'));
                                          this_.updateJumoAmount();
                                          this_.updateTotal();
                                      });
    },

    changeDonationAmount: function(amount, selectedReward, dontUpdateJumoAmount) {
        var donationAmount = this.inputToNumber(amount, selectedReward);        
        var jumoAmount = this.getJumoAmount();

        this.setDonationInputVal(donationAmount);
        this.setJumoInputVal(jumoAmount);
        
        if (!dontUpdateJumoAmount) {
            this.updateJumoAmount();            
        }

        this.updateTotal();
        // check donation amount and validate rewards
    },

    updateTotal:function() {
        if (!this.donationAmount) {
            this.setDonationAmount(0);            
        }
        
        if (!this.jumoAmount) {
            this.setJumoAmount(0);
        }

        if (this.rewards) { 
            this.checkRewards(this.donationAmount);
        }

        var val = this.formatCommaSeparatedMoneyVal(this.donationAmount + this.jumoAmount);
        this.totalDiv.text("$" + val);
    },

    checkRewards: function(amount) {
        var selectedReward = jQuery('.rewards .selected');
        var minAmount = selectedReward.attr('data-val');

        if (selectedReward && minAmount && amount < minAmount) {
            selectedReward.find('.amount').css({ background: '#79AF2C' });
            setTimeout(function() { selectedReward.find('.amount').css({ background: 'none' }); }, 500);
        }
    },

    updateJumoAmount:function(){
        var donationAmount = this.getDonationAmount();

        this.setJumoInputVal(donationAmount * (this.jumoPercent / 100));
    },

    /** 
     * returns @string for value ie 12.22
     */
    formatMoneyVal: function(val){
        // rounds total to two decimal places
        var total = "" + ((Math.round(val * 100)) / 100);

        var dec1 = total.substring(total.length-3, total.length-2);
        var dec2 = total.substring(total.length-2, total.length-1);

        if (dec1 != '.') { // adds trailing zeroes if necessary
            if (dec2 == '.'){ total += "0"; }
        }
        return total;
    },
    /*
     * from http://www.willmaster.com/library/tutorials/currency-formatting-and-putting-commas-in-numbers-with-javascript-and-perl.php
     * ugliest js ive ever seen
     */
    formatCommaSeparatedMoneyVal: function(amount) {       
	    var delimiter = ",";
	    amount = String(amount);
        
	    var a = amount.split('.',2);
	    var d = a[1];
	    var i = parseInt(a[0]);
	    var minus = '';

	    if(isNaN(i)) { return ''; }
	    if(i < 0) { minus = '-'; }
	    i = Math.abs(i);
	    var n = new String(i);
	    a = [];
	    while (n.length > 3) {
		    var nn = n.substr(n.length-3);
		    a.unshift(nn);
		    n = n.substr(0,n.length-3);
	    }
        
	    if(n.length > 0) { a.unshift(n); }
	    n = a.join(delimiter);
        if (d) {
	        if (d.length < 1) { amount = n; }
            else if (d.length == 1) { amount = n + '.' + d + "0"; }     
	        else { amount = n + '.' + d.slice(0,2); }            
        }
	    amount = minus + amount;
	    return amount;
    },

    inputToNumber: function(val, input){
        try {
            var num = Number(val);      
            if (isNaN(num)) {
                return false; //this.showError(input, 'Please enter a proper number');
            } else {
                return num;
            }
        } catch (x) {
            // this.showError(input, 'Please enter a proper number');
            /*console.log(x);*/
        }
    },
    setReward:function(jObj) {
        jQuery('#id_reward').val(jObj.attr('data-id'));
    },   

    getDonationAmount: function(){
        return this.inputToNumber(this.donationDiv.val());
    },
    setDonationAmount: function(amount){
        if (amount > 20000){
            amount = 20000;
        } else if (amount < 0) {
            amount = 0;
        }

        this.donationAmount = amount;
        return amount;
    },
    setDonationInputVal: function(amount){
        amount = this.setDonationAmount(amount);
        this.donationDiv.val(this.formatMoneyVal(amount));
    },

    getJumoAmount: function() {
        return this.inputToNumber(this.jumoDonationDiv.val(), this.jumoDonationDiv);
    },
    setJumoAmount: function(amount){
        if (amount > 20000){
            amount = 20000;
        } else if (amount < 0) {
            amount = 0;
        }

        this.jumoAmount = amount;
        return amount;
    },

    setJumoInputVal: function(amount){
        amount = this.setJumoAmount(amount);
        this.jumoDonationDiv.val(this.formatMoneyVal(amount));
    },

    showError:function(div, error) {
        var message = error || "something went wrong while we were processing your payment";        
        this.errorDiv.text(message);
    },
    
    donate: function(jObj) {
        if (jObj.hasClass('disabled')){ return false; }
        return true;
    }
};