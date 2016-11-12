#!/usr/bin/python

import re
import sys
import robot
from easygui import multchoicebox as multichoice

def main():
    RobotRun()
 
#
class RobotRun(object):
    def __init__(self):
        self.get_arguments()
        self.proceed()
    
    def get_arguments(self):
        args = sys.argv[1:]
        self.proceed = self._run_tcs
        self.select = True
        if '-x' in args: 
            args.remove('-x')
            self.select = False
        if (not args) or ('-h' in args) or ('--h' in args): 
            self.proceed = self._help
            return
        self.suitefile = args.pop(0)

    def _help(self):
        print """\
Usage:
  python robotrun.py [-x] suite_file_name
  -x: run with previous selection"""

    def _run_tcs(self):
        suite = readfile(self.suitefile)
        tcs = self.tcs = get_tcs(suite)
        # read 'x' tags, combine somehow with prev_choice
        prev_choice = self.get_prev_choice()
        self.tcs2run = [tcs[i]  for i in prev_choice if i<len(tcs)]
        if self.select:
            self.tcs2run = multichoice( 
                msg='Select testcases to run', 
                title='RobotRun ' + self.suitefile,
                choices=tcs,
                preselect=prev_choice )
            self.save_selection()
        self._execute()

    def _run_previous(self):
        self.tcs2run = self.prev_choice

    def _execute(self):
        failers = robot.run(self.suitefile, test=self.tcs2run, loglevel="TRACE", consolecolors="ON")
    
    def get_prev_choice(self):
        return eval( readfile(self.selection_file, default='[]') )

    @property
    def selection_file(self):
        return self.suitefile + '.sel'

    def save_selection(self):
        tc_indices = [self.tcs.index(tc)  for tc in self.tcs2run]
        with open(self.selection_file, 'w') as f:
            f.write(repr(tc_indices))

#
def get_tcs(suite):
    match_tc_section = re.search(r'(?is)[\n|^]\*+ ?test ?cases? ?\*+(.*?)(\n\*|$)', suite)
    if not match_tc_section: return
    tc_section = match_tc_section.group(1)

    tcs = [ match_tc.group(1)
              for match_tc in re.finditer(r'(?m)^(\w.*?)(?: {3,}|\t|\n)', tc_section) ]
    return tcs

    
#
def readfile(fname, default=None):
   try:
       with open(fname) as f:
           return f.read()
   except IOError as e:
       if default is None: raise
       return default

# -----------------------------

if __name__ == '__main__':
    main()
