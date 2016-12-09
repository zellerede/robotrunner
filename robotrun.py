#!/usr/bin/python

import os
import sys
from subprocess import Popen, PIPE

try:
    from wmctrl import Window
except ImportError:
    # wmctrl functionality is not a must just nice-to-have
    from no_wmctrl import Window

CURDIR = os.path.dirname(__file__)
ROBOTRUNNER = os.path.join(CURDIR, 'robotrunner.py')

def main():
    RobotRun_Control()

# ----------------------------

class RobotRun_Control(object):
    """
Simple GUI for selecting and running robot testcases,
I'm specifically its controller for IDE's

Usage from inside an IDE:
  python -u robotrun.py suite_file_name
"""
    def __init__(self):
        self.get_arguments()
        self.proceed()
    
    def get_arguments(self):
        args = sys.argv[1:] # ['test.tsv'] # 
        self.proceed = self.controller
        if (not args) or ('-h' in args) or ('--h' in args): 
            self.proceed = self.help
            return
        self.suitefile = args.pop(0)

    def help(self):
        print self.__doc__
    
    def controller(self):
        if self.recalled():
            self.send_back_console()
            return
        Popen([sys.executable, ROBOTRUNNER, self.suitefile])

    def send_back_console(self):
        try:
            #with open(self.ext_pipe) as out:
            #    for line in iter(out.readline, b''): 
            #        print line.rstrip()
            print readfile(self.ext_pipe) # can we make it continuously streaming?
        except IOError as e:
            if 'No such file' not in str(e):
                print e

    #
    @property
    def rrun_file(self):
        return self.suitefile + '.rrun'

    @property
    def ext_pipe(self):
        return self.suitefile + '.pipe'

    def recalled(self):
        if not os.path.isfile(self.rrun_file):
            return
        try: 
            window_id_hex = readfile(self.rrun_file)
            if window_id_hex.startswith('run'): 
                return True  # but we can't switch to the running window
            im_running = Window.by_id( int(window_id_hex,16) )
        except Exception as e:
            print e  ###
            return
        if im_running:
            writefile(self.rrun_file, 'run baby')
            im_running[0].activate()
            return True

#
def readfile(fname):
    with open(fname) as f:
        return f.read()

def writefile(fname, content):
    try:
        with open(fname, 'w') as f:
            f.write(content)
    except IOError as e:
        print e

# -------------------------------

if __name__ == '__main__':
    main()
