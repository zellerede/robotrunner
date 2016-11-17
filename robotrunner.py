#!/usr/bin/python

import wx
import re
import sys
import robot
from StringIO import StringIO


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
        args = sys.argv[1:] # ['test.tsv'] # 
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

def calc_size():
    maxX, maxY = wx.GetDisplaySize()
    return (min(maxX*3//5, maxY), maxY*2//3)

class RobotRun_GUI(wx.Frame):
    def __init__(self, app):
        wx.Frame.__init__(self, parent=None, title='RobotRun', size=calc_size()) # + testsuite name
        self.app = app
        self.build()
        self.Centre()
        self.Show()

    def build(self):
        self.add_toolbar()
        self.setup_panel()
        self.add_listbox()
        self.add_resultbox()

    def add_toolbar(self):
        tb = self.CreateToolBar(wx.TB_RIGHT)
        play = tb.AddLabelTool(wx.ID_RETRY, 'run', wx.Bitmap('play.png'))
        self.Bind(wx.EVT_TOOL, self.on_play, play)
        tb.AddSeparator()
        tb.Realize()
    
    def setup_panel(self):
        self.panel = wx.Panel(self)
        self.place = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.place)

    def add_listbox(self):
        self.lb = wx.ListBox(self.panel, style=wx.LB_MULTIPLE, choices=self.app.tcs)
        self.place.Add(self.lb, flag=wx.EXPAND|wx.ALIGN_LEFT)

    def add_resultbox(self):
        self.resultBox = wx.StaticText(self.panel, label='(results come here)')
        self.place.Add(self.resultBox, flag=wx.SHAPED|wx.ALIGN_RIGHT)

    def on_play(self, e):
        tcs2run = [self.app.tcs[i] for i in self.lb.GetSelections()]
        result = StringIO()
        failers = robot.run(self.app.suitefile, test=tcs2run, loglevel="TRACE", stdout=result) #, consolecolors="ON")
        self.resultBox.SetLabel( result.getvalue() )


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
