#!/usr/bin/python

"""
    Modified version of http://twistedmatrix.com/trac/browser/tags/releases/twisted-8.1.0/doc/core/examples/cursesclient.py


    This is an example of integrating curses with the twisted underlying    
    select loop. Most of what is in this is insignificant -- the main piece 
    of interest is the 'CursesStdIO' class.                                 

    This class acts as file-descriptor 0, and is scheduled with the twisted
    select loop via reactor.addReader (once the curses class extends it
    of course). When there is input waiting doRead is called, and any
    input-oriented curses calls (ie. getch()) should be executed within this
    block.

    Remember to call nodelay(1) in curses, to make getch() non-blocking.
"""

# System Imports
import curses, sys
import curses.wrapper, curses.textpad

# Twisted imports
from twisted.internet import reactor

class CursesStdIO :
    """fake fd to be registered as a reader with the twisted reactor.
       Curses classes needing input should extend this"""

    def fileno (self) :
        """ We want to select on FD 0 """
        return 0

    def doRead (self) :
        """called when input is ready"""

    def logPrefix (self) : 
        return 'CursesClient'

class IOWrapper (object) :
    def __init__ (self, console, label) :
        self.console = console
        self.label = label
        
    def write (self, bytes) :
        self.console.writeLine("[%s] %s" % (self.label, bytes))

class Console (CursesStdIO) :
    """
        This is meant to function as a simple interactive console.

        At the bottom there is a single line used to input commands.

        The rest of the display is used to display lines of output
    """
    
    prompt = ""

    def __init__ (self, stdscr) :
        self.stdscr = stdscr

        # make input calls non-blocking
        self.stdscr.nodelay(1) 
        
        # read chars one by one?
        curses.cbreak()
        
        # we handle this ourself
        curses.noecho()

        # have curses interpret various weird keycodes
        self.stdscr.keypad(1)
        
        # window height and width
        self.rows, self.cols = self.stdscr.getmaxyx()

        # output line buffer
        self.outputLines = []
        
        # uuh, do we need colours?
        curses.start_color()

        # create color pair's 1 and 2
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

        # output window
        self.output_win = self.stdscr.subwin(self.rows - 2, self.cols, 0, 0)
        self.output_win.setscrreg(0, self.rows - 3)
        self.output_win.idlok(1)
        self.output_win.scrollok(1)

        # status window
        self.status_win = self.stdscr.subwin(1, self.cols, self.rows - 2, 0)

        # input window
        self.input_win = self.stdscr.subwin(1, self.cols, self.rows - 1, 0)
        self.input_textbox = curses.textpad.Textbox(self.input_win)
        self.input_win.attrset(0)
        self.input_win.standend()

        self.drawStatus()
        self.prepInput()

    def connectionLost (self, reason) :
        self.close()

    def writeLine (self, line) :
        """ add a line to the internal list of lines"""

        self.outputLines.append(line)

        self.output_win.move(0, 0)
        self.output_win.insdelln(-1)
        self.output_win.addstr(self.rows - 3, 0, line)
        self.output_win.refresh()
    
    def drawStatus (self) :
        status = " [status] "

        assert len(status) <= self.cols
        
        try :
            self.status_win.addstr(0, 0, "%-*s" % (self.cols, status), curses.A_REVERSE)
        except curses.error :
            pass

        self.status_win.refresh()
    
    def prepInput (self) :
        # doesn't work properly for some reason
        curses.flash()

        self.input_win.clear()
        self.input_win.addstr(0, 0, self.prompt)
        self.input_win.refresh()

    def doRead (self) :
        """ Input is ready! """

        # read a character
        ch = self.stdscr.getch() 

        # pass it to the input textbox
        if not self.input_textbox.do_command(ch) :
            # a complete line
            line = self.input_textbox.gather()[len(self.prompt):]
            
            self.input_win.clear()

            self.lineReceived(line)

            self.prepInput()
        
        self.input_win.refresh()
    
    def lineReceived (self, line) :
        self.writeLine("You said: %s" % line)

    def close (self) :
        """ clean up """

        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

def main (console_cls, cb) :
    """
        Runs the reactor inside curses.wrapper, using the given console class to do the curses console stuff
    """

    curses.wrapper(_main, console_cls, cb)

def _main (stdscr, console_cls, cb) :
    screen = console_cls(stdscr)

    reactor.addReader(screen)

    stdscr.refresh()

    cb(screen)

    reactor.run()

if __name__ == '__main__' :
    main(Console, lambda x: None)

