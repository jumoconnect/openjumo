var FORMS = {
    verify: [{
		         id: 'username',
		         name: 'Your Name',
		         type: 'tweet',
		         required: true,
		         val: "{{ user.get_name }}"
	         },{
		         id: 'email',
		         name: 'Your Email',
		         type: 'email',
		         required: true,
		         val: "{{ user.email }}"
	         } ,{
		         id: 'affiliation',
		         name: 'Your Affiliation',
		         type: 'tweet',
		         required: true,
		         val: ""
	         } ,{
		         id: 'phone',
		         name: 'Phone Number',
		         type: 'tweet',
		         required: false,
		         val: ""
	         }]
};

var FORMS_SEED = {
    verify: [{
		         id: 'email',
		         name: 'Your Email',
		         type: 'email',
		         required: true,
		         val: "{{ user.email }}"
	         },{
		         id: 'affiliation',
		         name: 'Your Affiliation',
		         type: 'tweet',
		         required: true,
		         val: ""
	         }]
};

