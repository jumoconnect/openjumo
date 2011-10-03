var About = ({
                 initialize: function(type, formTypes) {
                     this.type = JUMO.Util.getHash() || type;
                     this.formTypes = formTypes || ['about', 'team', 'contact'];
                     JUMO.Util.showhideTabs(this.type, this.formTypes);
                     this.setupMouseEvents();
                 },
                 setupMouseEvents: function(){
                      var this_ = this;

                      var formNav = jQuery('#section_nav')
                         .find('a')
                         .click(function(event){
                                    event.stopPropagation();
                                    this_.type = jQuery(this).attr('class'); // active type
                                    JUMO.Util.showhideTabs(this_.type, this_.formTypes);
                                    return false;
                                }).end();
                 }
             });