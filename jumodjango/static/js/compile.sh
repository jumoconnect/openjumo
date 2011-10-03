#!/bin/bash
java -jar compiler.jar --js=base.src.js --js=lib.js --js=util.js --js=modules/popup.js --js=modules/search.js --js=modules/tracking.js --js_output_file=base.js
java -jar compiler.jar --js=setup.src.js --js_output_file=setup.js
java -jar compiler.jar --js=forms.src.js --js_output_file=forms.js
java -jar compiler.jar --js=discover.src.js --js_output_file=discover.js
java -jar compiler.jar --js=categorydiscover.src.js --js_output_file=categorydiscover.js
java -jar compiler.jar --js=donate.src.js --js_output_file=donate.js
java -jar compiler.jar --js=login.src.js --js_output_file=login.js
java -jar compiler.jar --js=search.src.js --js_output_file=search.js
