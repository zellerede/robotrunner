#!/usr/bin/python

import wx
import re
import os
import sys
import robot
from StringIO import StringIO

try:
    from wmctrl import Window
except ImportError:
    # wmctrl functionality is not a must just nice-to-have
    from no_wmctrl import Window

def main():
    RobotRun()

# ----------------------------

class RobotRun(wx.App):
    """
Simple GUI for selecting and running robot testcases

Usage:
  python robotrunner.py suite_file_name
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
        if self.recalled(): return
        self.tcs = get_tcs(self.suitefile)
        if not self.tcs:
            print "No test cases identified in the suite."
            return
        try:
            self.init_dialog()
        finally:
            try: os.unlink(self.rrun_file)
            except IOError as e:
                if "No such file" not in str(e):
                    print e
    
    def init_dialog(self):
        wx.App.__init__(self)
        self.frame = RobotRun_GUI(self)
        self.MainLoop()

    def run(self, selection):
        tcs2run = [self.tcs[i] for i in selection]
        if not tcs2run: return
        result = StringIO()
        failed = robot.run(self.suitefile, test=tcs2run, loglevel="TRACE", stdout=result) #, consolecolors="ON")
        return (failed, result.getvalue())
    
    #
    @property
    def rrun_file(self):
        return self.suitefile + '.rrun'

    def recalled(self):
        if not os.path.isfile(self.rrun_file):
            return
        im_running = False
        try: 
            window_id_hex = readfile(self.rrun_file)
            im_running = Window.by_id( int(window_id_hex,16) )
        except Exception as e:
            print e  ###
            return
        if im_running:
            writefile(self.rrun_file, 'run baby')
            im_running[0].activate()
            return True

# --------------------------

def calc_size():
    maxX, maxY = wx.GetDisplaySize()
    return (min(maxX*3//5, maxY), maxY*2//3)

def icon_for(png):
    curdir = os.path.dirname(__file__)
    return wx.Bitmap( os.path.join(curdir, png) )

def green_or_red(failed, total):
    green = (0, 0xFF, 0) #(0x20, 0xEF, 0x20) # RGB
    if not failed:
        return wx.Colour(*green)
    red = (0xFF, 0x40, 0x40)
    not_that_green = (0xAD, 0xFF, 0x00)
    passed = total - failed
    result_color = [(failed*r + passed*g) // total 
                       for g,r in zip(not_that_green, red)]
    return wx.Colour(*result_color)

# --------------------------

class RobotRun_GUI(wx.Frame):
    def __init__(self, app):
        wx.Frame.__init__(self, parent=None, title='RobotRun', size=calc_size()) # + testsuite name
        self.app = app
        self.load_icons()
        self.build()
        self.Centre()
        self.Show()
    
    def load_icons(self):
        self.PLAY_ICON = icon_for('play.png')
        # [refresh] reload TC list
        # [antired] Set background colour to original
        # Play all
        # Open logs
        # Trace level, variables [+todo: Find out local_ip variable for me]

    def build(self):
        self.Bind(wx.EVT_ACTIVATE, self.on_reenter)
        self.add_toolbar()
        self.setup_panel()
        self.add_listbox()
        self.add_resultbox()

    def add_toolbar(self):
        tb = self.CreateToolBar(wx.TB_RIGHT | wx.TB_DOCKABLE)
        play = tb.AddLabelTool(wx.ID_RETRY, 'run', self.PLAY_ICON)
        #play.SetToolTip( wx.ToolTip("([{RUN}])") )
        self.Bind(wx.EVT_TOOL, self.on_play, play)
        #tb.Bind(wx.EVT_KEY_UP, self.on_keypress)
        tb.AddSeparator()
        tb.Realize()
    
    def setup_panel(self):
        self.panel = wx.Panel(self)
        self.original_bkg = self.panel.GetBackgroundColour()
        self.place = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.place)

    def add_listbox(self):
        self.lb = wx.ListBox(self.panel, style=wx.LB_MULTIPLE, choices=self.app.tcs)
        self.lb.Bind(wx.EVT_KEY_UP, self.on_keypress)
        self.place.Add(self.lb, flag=wx.EXPAND|wx.ALIGN_LEFT)
    
    def add_resultbox(self):
        self.resultBox = wx.StaticText(self.panel, label='(results come here)')
        self.place.Add(self.resultBox, flag=wx.SHAPED|wx.ALIGN_RIGHT)
    
    #
    def on_play(self, event=None):
        selection = self.lb.GetSelections()
        if selection:
            self.resultBox.SetLabel( '(executing...)' )
            self.panel.SetBackgroundColour( self.original_bkg )
            failed, result = self.app.run( selection )
            self.resultBox.SetLabel( result )
            self.panel.SetBackgroundColour( green_or_red(failed, len(selection)) )
    
    def on_keypress(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN:
            self.on_play(event)
        event.Skip()
    
    def on_reenter(self, event):
        if event.GetActive():
            rrun_file = self.app.rrun_file
            try:
                if not os.path.isfile(rrun_file):
                    self.save_my_window_id(rrun_file)
                    return
                rrun = readfile(rrun_file)
            except IOError as e:
                print e
                return
            if rrun.startswith('run'):
                self.save_my_window_id(rrun_file)
                self.on_play()
    
    def save_my_window_id(self, rrun_file):
        writefile(rrun_file, Window.get_active().id)


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

def writefile(fname, content):
    try:
        with open(fname, 'w') as f:
            f.write(content)
    except IOError as e:
        print e

# -------------------------------

if __name__ == '__main__':
    main()
