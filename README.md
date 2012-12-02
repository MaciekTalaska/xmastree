**Author** Maciej Talaska. [Follow me on Twitter][twitter]

[![Build Status](https://secure.travis-ci.org/MaciekTalaska/xmastree.png?branch=master)](https://travis-ci.org/MaciekTalaska/xmastree)


xmastree 
========

How to install?
---------------
1. Grab Python interpreter for your machine/OS (stick to Python 2.x)
2. Install python setuptools (http://pypi.python.org/pypi/setuptools)
3. Install Tornado Web Server: "easy_install tornado"

Please note that easy_install is installed into Python's scripts 
folder, so if Python was installed into C:\Python on your machine
you should navigate to C:\Python\scripts before trying to invoke
easy_install.

How to run?
-----------
1. python xmastree.py


How to check that it works properly on your machine?
----------------------------------------------------
1. Start server: python xmastree.py
2. Run tests: python -m server_api_tests

[twitter]: https://twitter.com/MaciekTalaska
