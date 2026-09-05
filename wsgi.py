import sys
import os

path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

os.chdir(path)

from mobile_server import app as application
