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
import curses
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

class Console (CursesStdIO) :
    """
        This is meant to function as a simple interactive console.

        At the bottom there is a single line used to input commands.

        The rest of the display is used to display lines of output
    """

    def __init__ (self, stdscr) :
        self.timer = 0
        self.statusText = "TEST CURSES APP -"
        self.searchText = ''
        self.stdscr = stdscr

        # set screen attributes

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

        # main window
        self.output_win = self.stdscr.subwin(self.rows - 1, self.cols, 0, 0)
        self.output_win.setscrreg(0, self.rows - 3)
        self.output_win.idlok(1)
        self.output_win.scrollok(1)

        # input window
        self.input_win = self.stdscr.subwin(1, self.cols, self.rows - 1, 0)
        self.input_textbox = curses.textpad.Textbox(self.input_win)

        self.drawStatus()

    def connectionLost (self, reason) :
        self.close()

    def addLine (self, line) :
        """ add a line to the internal list of lines"""

        self.outputLines.append(line)

        self.output_win.move(0, 0)
        self.output_win.insdelln(-1)
        self.output_win.addstr(self.rows - 3, 0, line)
        self.output_win.refresh()
    
    def drawStatus (self) :
        status = " [status]   blaa         ---- "

        assert len(status) <= self.cols

        self.output_win.addstr(self.rows - 2, 0, "%*s" % (self.cols, status), curses.A_REVERSE)
        self.output_win.refresh()

    def doRead (self) :
        """ Input is ready! """

        # read a character
        ch = self.stdscr.getch() 

        # pass it to the input textbox
        if not self.input_textbox.do_command(ch) :
            # a complete line
            line = self.input_textbox.gather()

            self.input_win.clear()

            self.handleLine(line)
        
        self.input_win.refresh()


        self.stdscr.addstr(self.rows-1, 0, self.searchText + (' ' * (self.cols-len(self.searchText)-2)))
        self.stdscr.move(self.rows-1, len(self.searchText))

        self.paintStatus(self.statusText + ' %d' % len(self.searchText))
        self.stdscr.refresh()
    
    def handleLine (self, line) :
        pass

    def close (self) :
        """ clean up """

        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

def main (stdscr) :
    
    screen = Console(stdscr)   # create Screen object
    stdscr.refresh()

    reactor.run()

if __name__ == '__main__' :
    curses.wrapper.wrapper(main)

