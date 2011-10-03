{% load tags %}

{% if entity.get_all_issues %}
var CONTEXTTAGS = [{% for issue in entity.get_all_issues %}{'name' : {% json_encode issue.name %}, 'tag_rank' : {% if issue.rank %}{{ issue.rank }}{% else %}1{% endif %}, 'type' : 'context'}{% if not forloop.last %},{% endif %}{% endfor %}];
{% else %}
var CONTEXTTAGS = [];
{% endif %}

{% if entity.get_working_locations %}
var GEOTAGS = [{% for location in entity.get_working_locations %}{% json_encode location %}{% if not forloop.last %},{% endif %}{% endfor %}];
{% else %}
var GEOTAGS = [];
{% endif %}


var ORGTAGS = [];


var FORMS = {
    about: [{
                id: 'name',
                name: 'Organization Name',
                type: 'tweet',
                required: true,
                val: {% json_encode entity.name %}
            },{
                id: 'handle',
                name: 'Organization Username',
                type: 'tweet',
                required: true,
                placeholder: 'pih',
                help: "Your organizations unique username used for your public Jumo page: www.jumo.com/USERNAME",
                val: {% json_encode entity.handle %}
            },{
                id:'ein',
                name: 'EIN',
                type: 'ein',
                required: false,
                placeholder: '12345678',
                val: '{% if entity.ein %}{{ entity.ein }}{% endif %}',
                help: "*Not required, but must be provided for 501(c)(3)\'s that wish to receive donations on Jumo. Find your organization's EIN <a href=\"http://nccsdataweb.urban.org/PubApps/990search.php?a=a&bmf=1\" target=\"_blank\">here</a>."
            },{
                id:'location',
                name: 'Headquarters',
                type: 'location',
                required: false,
                val: {% if entity.location %}{% json_encode entity.location %}{% else %}''{% endif %}
	        },{
                id: 'vision_statement',
                name: 'Vision Statement',
                type: 'tweet',
                required: false,
                tip: "", //<b>200</b> characters remaining",
                counter: true,
                max_length: 250,
                placeholder: "In one sentence, describe your organization's vision",
                val: {% json_encode entity.vision_statement %}
            },{
                id: 'mission_statement',
                name: 'Mission Statement',
                type: 'text',
                required: false,
                placeholder: "How does your organization seek to accomplish its vision?",
                val: {% json_encode entity.mission_statement %}
            },{
                id: 'working_locations',
                name: 'Working In',
                type: 'multi_location',
                required: false,
                val: GEOTAGS,
                help: "Enter the cities or countries in which you work."
            },{
                id: 'context',
                name: 'Working On',
                type: 'dependent_select',
                required: false,
                val: CONTEXTTAGS,
                sub: 'tags',
                help: 'Choose tags from the far right dropdown that describe your work. Please list in order of importance.'
            }],
    connect: [{
                  id: 'facebook_id',
                  name: 'Facebook ID',
                  type: 'fbid',
                  required: false,
                  placeholder: "1234567890",
                  val: {% json_encode entity.facebook_id %},
                  help: "Please enter a valid Facebook id or a link to your facebook page"
              },{
			      id: 'fb_fetch_enabled',
			      name: 'Facebook',
			      type: 'checkbox',
			      required: false,
			      val: '{{ entity.fb_fetch_enabled }}',
			      text:"Enable JUMO to pull your updates from your Facebook page"
              },{
                  id: 'url',
                  name: 'Website',
                  type: 'url',
                  required: false,
                  placeholder: "http://www.your.org",
                  val: '{{ entity.url }}'
              },{
                  id:'email',
                  name: 'Email',
                  type: 'email',
                  required: false,
                  placeholder: "example@your.org",
                  val: '{{ entity.email }}'
              },{
                  id: 'phone_number',
                  name: 'Phone',
                  type: 'phone',
                  required: false,
                  placeholder: "(555) 555-5555",
                  val: {% json_encode entity.phone_number %}
              },{
                  id: 'twitter_id',
                  name: 'Twitter',
                  type: 'twitterid',
                  required: false,
                  placeholder: '@yourorg',
                  val: {% json_encode entity.twitter_id %}
              },{
			      id: 'twitter_fetch_enabled',
			      name: 'Twitter fetch',
			      type: 'checkbox',
			      required: false,
			      val: '{{ entity.twitter_fetch_enabled }}',
			      text:"Enable JUMO to pull content from your Twitter account"
              },{
                  id: 'blog_url',
                  name: 'Blog',
                  type: 'url',
                  required: false,
                  placeholder: 'http://your.org/blog',
                  val: {% json_encode entity.blog_url %}
              },{
                  id: 'youtube_id',
                  name: 'Youtube Username',
                  type: 'tweet',
                  required: false,
                  placeholder: 'yourorg',
                  val: {% json_encode entity.youtube_id %}
              },{
                  id: 'flickr_id',
                  name: 'Flickr Username',
                  type: 'tweet',
                  required: false,
                  placeholder: 'yourorg',
                  val: {% json_encode entity.flickr_id %}
              },{
                  id: 'vimeo_id',
                  name: 'Vimeo Username',
                  type: 'tweet',
                  required: false,
                  placeholder: 'yourorg',
                  val: {% json_encode entity.vimeo_id %}
              }],
    more: [{
               id:'img_url',
               name: 'Image URL',
               type: 'url',
               required: false,
               placeholder: "www.example.com/image/logo.png",
               help: "If your organization does not have a Facebook profile or if you want a custom logo on your organization profile, enter the image URL here.",
               extra_help: "In your web browser, right click on the picture you want to select and select 'copy image location'. Paste that URL in this text box",
               val: {% json_encode entity.img_url %}
           }, {
               id: 'methods',
               name: 'Methods',
               type: 'multi_select',
               required: false,
               val: [{% for method in methods %}{% json_encode method.method %}{% if not forloop.last %},{% endif %}{% endfor %}],
               options: [{
                             val: 'advocacy'
                         }, {
                             val: 'direct service'
                         }, {
                             val: 'grantmaking'
                         }, {
                             val: 'infrastructure'
                         }]
           },{
               id: 'size',
               name: '# of Employees',
               type: 'select',
               required: false,
               val: '{{ entity.size }}',
               options: [{
                             val: ""
                         },{
                             val: "1-10"
                         },{
                             val: "10-50"
                         },{
                             val: "51-100"
                         },{
                             val: "100+"
                         }]
           },{
               id: 'revenue',
               name: 'Revenue Size',
               type: 'select',
               required: false,
               val: '{{ entity.revenue }}',
               options: [{
                             val: ""
                         },{
                             val: "less than $100,000"
                         },{
                             val: "$100,000 - $1,000,000"
                         },{
                             val: "$1m - $5m"
                         },{
                             val: "$5m - $20m"
                         },{
                             val: "more than $20m"
                         }]
           },{
               id: 'year_founded',
               name: 'Year Founded',
               type: 'year',
               required: false,
               placeholder: '1992',
               val: {% if entity.year_founded %}{{ entity.year_founded }}{% else %}""{% endif %}
           },{
               id: 'accomplishments',
               name: 'Key Facts',
               type: 'accomplishments',
               required: true,
               val: [ {% for acc in accomplishments %}{ year : {% json_encode acc.header %}, text : {% json_encode acc.description %}, link : '{{ acc.link }}'}{% if not forloop.last %},{% endif %}{% endfor %} ]
           }]
};


/**
 *
 {% if entity.parent_org %} 
               id:'parent_orgs',
               name: 'A Program of',
		       type: 'org_search',
		       required: false,
               'data-val': "{{ entity.parent_org.id }}",
		       val: {% json_encode entity.parent_org.name %},
               restrictType: "org",
               {% else %}
		       id:'parent_orgs',
               name: 'A Program of',
		       type: 'org_search',
		       required: false,
		       val: "",
               placeholder: "e.g., Habitat for Humanity",
               restrictType: "org",
               {% endif %}
               tip: "Is this a project or program of a larger organization?"
	       },{
               {% if entity.parentorg.all %}
		       id:'child_orgs',
               name: 'Affiliated Programs',
		       type: 'multi_org_search',
		       required: false,
               'data-val': [{% for child in entity.parentorg.all %}"{{ child.id }}"{% if not forloop.last %},{% endif %}{% endfor %}],
               'val': [{% for child in entity.parentorg.all %}{% json_encode child.name %}{% if not forloop.last %},{% endif %}{% endfor %}],
               restrictType: "org",
               help: "Does this organization have multiple projects or programs on Jumo?"
           },{
               {% else %}
		       id:'child_orgs',
               name: 'Affiliated Programs',
		       type: 'multi_org_search',
		       required: false,
               'data-val': [],
		       val: "",
               restrictType: "org",
               placeholder: "Habitat for Humanity Ghana",
               help: "Does this organization have multiple projects or programs on Jumo?"
           },{
 {% endif %}
 */