**Author** Maciej Talaska. [Follow me on Twitter][twitter]

[![Build Status](https://secure.travis-ci.org/MaciekTalaska/xmastree.png?branch=master)](https://travis-ci.org/MaciekTalaska/xmastree)


xmastree 
========

How to install?
---------------
1. Install Python interpreter. Xmastree has been tested against following Python versions:
 - Python 2.7
 - Python 3.4
 - Python 3.5
 - Python 3.6
2. Install python package manager. Choose one that you prefer: 
 - setuptools (http://pypi.python.org/pypi/setuptools)
 - pip (https://pip.pypa.io/en/stable/installing/)
3. Install Tornado Web Server: 
 - `easy_install tornado` if using setuptools
 - `pip install tornado` if using pip

**Note:** the project uses Tornado 5.0.2 at the moment. If you encounter any problems try to get this specific version and check if that works for you.

**Note for Windows users:** easy_install is installed into Python's scripts 
folder, so if Python was installed into C:\Python on your machine
you should navigate to C:\Python\scripts before trying to invoke
easy_install.

How to run?
-----------
1. `python xmastree.py`


How to check that it works properly on your machine?
----------------------------------------------------
1. Start server: `python xmastree.py`
2. Run tests: `python server_api_tests`

[twitter]: https://twitter.com/MaciekTalaska
