#!/usr/bin/python

import wx
import re
import os
import sys
import robot
from StringIO import StringIO

from socket import socket, AF_INET, SOCK_DGRAM, error as SocketError # for get_my_ip()
import webbrowser

try:
    from wmctrl import Window
except ImportError:
    # wmctrl functionality is not a must just nice-to-have
    from no_wmctrl import Window

CURDIR = os.path.dirname(__file__)

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
        self.tcs = get_tcs(self.suitefile)
        if not self.tcs:
            print "No test cases identified in the suite."
            return

        try:
            os.mkfifo(self.ext_pipe)
        except OSError as e:
            if "File exists" not in str(e):
                print "mkfifo error"
                print e
        except AttributeError as e:
            "No immediate console piping is supported." # win

        try:
            #################
            self.init_gui() #
            #################
        finally:
            try: 
                os.unlink(self.rrun_file)
                os.unlink(self.ext_pipe)
            except OSError as e:
                if e.errno != 2:
                    print e
    
    def init_gui(self):
        wx.App.__init__(self)
        self.gui = RobotRun_GUI(self)
        self.MainLoop()

    def run(self, selection):
        tcs2run = [self.tcs[i] for i in selection]
        if not tcs2run: return
        result = StringIO()
        failed = robot.run(self.suitefile, 
                           test=tcs2run, 
                           log=self.log_html, 
                           loglevel="TRACE", 
                           variable = ['local_ip:' + get_my_ip()], 
                           stdout=result,
                           listener=Follow(self.gui))
        return (failed, result.getvalue())

    def reload(self):
        self.tcs = get_tcs(self.suitefile)
        return self.tcs

    #
    @property
    def rrun_file(self):
        return self.suitefile + '.rrun'

    @property
    def ext_pipe(self):
        return self.suitefile + '.pipe'
    
    @property
    def log_html(self):
        return os.path.join(os.path.dirname(self.suitefile), 'log.html')

# --------------------------

def calc_size():
    maxX, maxY = wx.GetDisplaySize()
    return (min(maxX*3//5, maxY), maxY*2//3)

def icon_for(png):
    return wx.Bitmap( os.path.join(CURDIR, png) )

def black_or_white(color):
    black = (0, 0, 0)
    white = (0xFF, 0xFF, 0xFF)
    brightness = color.red * 0.299 + color.green * 0.587 + color.blue * 0.114
    return wx.Colour(*black) if brightness>128 else wx.Colour(*white)

def get_my_ip():
    try:
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        name = s.getsockname()[0]
        s.close()
    except SocketError as e:
        name = ''
        if e.errno == 101: # Network is unreachable
            print "[WARN]    No internet connection, hence no ip address found."
        else:
            print e
    return name

# --------------------------

class RobotRun_GUI(wx.Frame):
    green = (0, 0xFF, 0) #(0x20, 0xEF, 0x20) # RGB
    red = (0xFF, 0x40, 0x40)
    almost_green = (0xAD, 0xFF, 0x00)

    INITIAL_MSG = '(results come here)'
    EXEC_KW = 'Executing keyword: '

    def __init__(self, app):
        title = 'RobotRun ' + re.sub(r'.*[/\\]|\..+', '', app.suitefile)
        wx.Frame.__init__(self, parent=None, title=title, size=calc_size()) # + testsuite name
        self.app = app
        self.build()
        self.Centre()
        self.Show()
    
    def load_icons(self):
        self.PLAY_ICON = icon_for('play.png')
        self.REFRESH_ICON = icon_for('refresh.png')
        self.OPEN_LOGS_ICON = icon_for('see_logs.png')
        # Play all
        # Trace level, variables

    def build(self):
        self.Bind(wx.EVT_ACTIVATE, self.on_reenter)
        self.load_icons()
        self.add_toolbar()
        self.setup_panel()
        self.add_listbox()
        self.add_resultbox()
        self.add_footer()

    def add_toolbar(self):
        tb = self.CreateToolBar(wx.TB_RIGHT | wx.TB_DOCKABLE)
        play = tb.AddLabelTool(wx.ID_RETRY, 'run', self.PLAY_ICON, shortHelp='Run selected tests')
        self.Bind(wx.EVT_TOOL, self.on_play, play)
        refresh = tb.AddLabelTool(wx.ID_REFRESH, 'refresh', self.REFRESH_ICON, shortHelp='Reload test suite')
        self.Bind(wx.EVT_TOOL, self.on_refresh, refresh)
        open_logs = tb.AddLabelTool(wx.ID_PREVIEW, 'preview', self.OPEN_LOGS_ICON, shortHelp='Open log.html')
        self.Bind(wx.EVT_TOOL, self.on_open_logs, open_logs)
        tb.AddSeparator()
        tb.Realize()
    
    def setup_panel(self):
        self.panel = wx.Panel(self)
        self.to_below = wx.BoxSizer(wx.VERTICAL)
        self.to_right = wx.BoxSizer(wx.HORIZONTAL)
        self.to_below.Add(self.to_right, 1)
        self.panel.SetSizer(self.to_below)
        #
        self.original_bkg = self.panel.GetBackgroundColour()
        self.set_font()

    def set_font(self):
        self.font = self.panel.GetFont()
        self.font.SetPointSize( 12 )
        self.panel.SetFont( self.font )
    
    def add_listbox(self):
        self.choose = wx.ListBox(self.panel, style=wx.LB_MULTIPLE, choices=self.app.tcs)
        # self.choose.SetSelection(0)
        self.choose.Bind(wx.EVT_KEY_UP, self.on_keypress)
        self.to_right.Add(self.choose, flag=wx.EXPAND|wx.ALIGN_LEFT)
    
    def add_resultbox(self):
        self.resultBox = wx.StaticText(self.panel, label=self.INITIAL_MSG, style=wx.VSCROLL|wx.HSCROLL)
        self.to_right.Add(self.resultBox, flag=wx.SHAPED|wx.EXPAND|wx.ALIGN_RIGHT)
    #
    def set_resultbox(self, text, color=None, append=False):
        if color is not None:
            self.panel.SetBackgroundColour( color )
            self.resultBox.SetForegroundColour( black_or_white(color) )
        prev = self.resultBox.GetLabel()  if append else  ''
        self.resultBox.SetLabel( prev + text )
        self.resultBox.Update()
        self.panel.Update()
        self.resultBox.Refresh()
        self.panel.Refresh()

    def add_footer(self):
        self.footer = wx.StaticText(self.panel, label=self.EXEC_KW + ' '*500)
        self.to_below.Add(self.footer, flag=wx.BOTTOM|wx.ALIGN_BOTTOM)

    def set_footer(self, text):
        self.footer.SetLabel( self.EXEC_KW + text )
        self.footer.Update()

    #    
    def on_play(self, event=None):
        selection = self.choose.GetSelections()
        if selection:
            #self.footer.Show()
            self.footer.Enable()
            self.set_resultbox('(executing...)', self.original_bkg)
            failed, result = self.app.run( selection )
            #self.footer.Hide()
            self.footer.Disable()
            self.set_resultbox( '-----\nDone\n\n', append=True )
   
    #
    def on_refresh(self, event=None):
        # reload
        self.set_resultbox(self.INITIAL_MSG, self.original_bkg)
        old_tc_list = self.app.tcs
        self.app.reload()
        if old_tc_list == self.app.tcs: return

        keep_selection = ()
        if ( len(old_tc_list) == len(self.app.tcs) and
             set(old_tc_list) != set(self.app.tcs) ):
           keep_selection = self.choose.GetSelections()
        self.choose.SetItems( self.app.tcs )
        for i in keep_selection:
            self.choose.SetSelection(i)

    def on_keypress(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN:
            self.on_play(event)
        event.Skip()
    
    def on_reenter(self, event):
        if not event.GetActive():
            return

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
            self.on_refresh()
            stdout = sys.__stdout__
            with open(self.app.ext_pipe, 'w') as output:
                sys.__stdout__ = output
                self.on_play()
            sys.__stdout__ = stdout
    
    def save_my_window_id(self, rrun_file):
        writefile(rrun_file, Window.get_active().id)

    def on_open_logs(self, event):
        wx.LaunchDefaultBrowser("file://"+self.app.log_html)

class Follow(object):
    ROBOT_LISTENER_API_VERSION = 2
    
    def __init__(self, gui):
        self.gui = gui
        self.passed = 0
        self.total = 0
        self.kw_chain = []

    def start_test(self, name, attr):
        self.gui.set_resultbox(
             text= "{}: ".format(name),
             append= (self.total>0) )

    def start_keyword(self, name, attr):
        name = re.sub(r'.*\.', '', name)
        self.kw_chain.append(name)
        self.gui.set_footer(' > '.join(self.kw_chain))

    def end_keyword(self, name, attr):
        if name not in self.kw_chain:
            #not supposed to be the case
            return
        while name!=self.kw_chain.pop(): 
            pass

    def end_test(self, name, attr):
        self.total += 1
        msg = attr.get('message') or attr.get('status')
        if attr['status']=='PASS':
            self.passed += 1
        else:
            msg = '[@!%&^]\n '+ msg
        self.gui.set_resultbox(
             text= " {}\n".format(msg),
             color= self.green_or_red(),
             append= True )
    
    def green_or_red(self):
        if (self.passed == self.total):
            return wx.Colour(*self.gui.green)
        total, passed = self.total, self.passed
        failed = total - passed
        result_color = [(failed*r + passed*g) // total 
                           for g,r in zip(self.gui.almost_green, self.gui.red)]
        return wx.Colour(*result_color)


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
