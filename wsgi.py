# PythonAnywhere WSGI entry point.
#
# On the "Web" tab of PythonAnywhere, open the WSGI configuration file it
# generated for you (something like
# /var/www/<your_username>_pythonanywhere_com_wsgi.py) and replace its
# contents with the lines below, adjusting the two paths for your username
# and the folder where you uploaded this project.
#
# ---------------------------------------------------------------------
# import sys
#
# project_home = '/home/<your_username>/agrinas_nicegui_dashboard/pythonanywhere_app'
# if project_home not in sys.path:
#     sys.path.insert(0, project_home)
#
# from app import app as application
# ---------------------------------------------------------------------
#
# This file mirrors that same snippet so `wsgi.py` also works if you point
# PythonAnywhere's WSGI file directly at it via an `execfile`/import, but the
# recommended path is copying the snippet above into PythonAnywhere's own
# generated WSGI file.

import os
import sys

project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application  # noqa: E402
