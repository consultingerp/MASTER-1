# Instructions for the Content API for Shopping Integration with odoo module

Before installing this module Install required liberay Pleas follow steps mentioned in link for more info
https://developers.google.com/api-client-library/python/start/installation 

pip (preferred):
$ pip install --upgrade google-api-python-client
      
Setuptools: Use the easy_install tool included in the setuptools package:
$ easy_install --upgrade google-api-python-client

#Generate Client id and Secreat id from google account
Create new project on google devloper api.

https://console.developers.google.com/apis

Then activate content api and after that go to "Credential" menu of api manager view for your project.

Open credential and in that "Authorized redirect URIs"

add URI: http://localhost:8069/google_content/authentication (for local)

Instead of http://localhost:8069 set your website url.