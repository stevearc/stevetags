Steve Tags
==========

Local Development
-----------------
First you need to `install Go <https://golang.org/doc/install>`_. We're using an asset
pipeline that I wrote in Go to compile coffeescript and less, and to bundle
everything.

Then you need docker (`sudo apt-get install docker.io && sudo adduser $USER docker`)

Then you ``./serve_forever.sh``

Deploy
------
You will need some global npm packages

```
npm install -g less uglify-js clean-css coffee-script
```
