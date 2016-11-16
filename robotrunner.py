#!/usr/bin/python

import wx
import re
import sys
import robot


def main():
    RobotRun()

# ----------------------------

class RobotRun(wx.App):
    """
Simple GUI for selecting and running robot testcases

Usage:
  python robotrun.py suite_file_name
"""
    def __init__(self):
        self.get_arguments()
        self.proceed()
    
    def get_arguments(self):
        args = sys.argv[1:]
        self.proceed = self.runner
        if (not args) or ('-h' in args) or ('--h' in args): 
            self.proceed = self.help
            return
        self.suitefile = args.pop(0)

    def help(self):
        print self.__doc__
    
    def runner(self):
        # if self.already_running()  # by an (empty) suitefile+'.rrun' existence
        #     self.frame.setInFocus() ...
        #     self.refresh()
        #     return
        self.tcs = get_tcs(self.suitefile)
        if not self.tcs:
            print "No test cases found to run."
            return
        self.init_dialog()
    
    def init_dialog(self):
        wx.App.__init__(self)
        self.frame = RobotRun_GUI(self)
        self.MainLoop()

# --------------------------

class RobotRun_GUI(wx.Frame):
    def __init__(self, app):
        wx.Frame.__init__(self, parent=None, title='RobotRun') # + testsuite name
        self.app = app
        self.build()
        self.Centre()
        self.Show()

    def build(self):
        self.add_toolbar()
        self.add_listbox()

    def add_toolbar(self):
        tb = self.CreateToolBar()
        play = tb.AddLabelTool(wx.ID_RETRY, 'run', wx.Bitmap('play.png'))
        self.Bind(wx.EVT_TOOL, self.on_play, play)
        tb.AddSeparator()
        tb.Realize()
    
    def add_listbox(self):
        self.lb = wx.ListBox(self, style=wx.LB_MULTIPLE, choices=self.app.tcs)

    def on_play(self, e):
        print self.lb.GetSelections()


# ----------------------------

def get_tcs(suitefile): # it would be more authentic to use robot's parser module...
    suite = readfile(suitefile)
    match_tc_section = re.search(r'(?is)[\n|^]\*+ ?test ?cases? ?\*+(.*?)(\n\*|$)', suite)
    if not match_tc_section: return
    tc_section = match_tc_section.group(1)

    tcs = [ match_tc.group(1)
              for match_tc in re.finditer(r'(?m)^(\w.*?)(?: {3,}|\t|\n)', tc_section) ]
    return tcs

    
def readfile(fname):
    with open(fname) as f:
        return f.read()

if __name__ == '__main__':
    main()
