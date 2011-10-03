#!/bin/bash

java -jar yuicompressor.jar --nomunge -o '.css$:-min.css' *.css # minify foo.css to foo-min.css
#java -jar yuicompressor.jar --nomunge -o '.css$:.css' *.css # minify foo.css to foo.css
