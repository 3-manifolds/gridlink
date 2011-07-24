#!/usr/bin/env python
#
#   Copyright (C) 2003-2007 Marc Culler and others
#
#   The URL for this program is:
#     http://math.uic.edu/~culler/gridlink/
#   This program is distributed under the terms of the 
#   GNU General Public License, version 2 or later, as published by
#   the Free Software Foundation.  See the file GPL.txt for details.
#   A copy of the license file may be found at:
#     ftp://ftp.math.uic.edu/pub/t3m/gridlink/GPL.txt
#   A README file is available at:
#     ftp://ftp.math.uic.edu/pub/t3m/gridlink/README
#   A current version of the source code is located in the same 
#   directory.
#
#   The development of this program was partially supported by
#   the National Science Foundation under grants DMS0608567,
#   DMS0504975 and DMS0204142.
#
#   $Author: culler $ $Date: 2007/03/28 20:00:37 $ $Revision: 1.75 $
#

import sys, os, webbrowser
from urllib import pathname2url
from random import randint
from Tkinter import *
from tkFileDialog import *
import tkSimpleDialog
from tkMessageBox import showinfo, showwarning
from gridlink_data import *
try:
    from hfk import *
except:
    TkHFK=None

revision = '$Revision: 1.75 $'.replace('$','')

class GridlinkApp:
    """
    Top level application which launches Gridlinks.
    Hides itself when active Gridlinks are present.
    """
    def __init__(self):
        self.windows = []
        self.root = Tk()
        self.root.title('Gridlink')
        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        self.newmenu = Menu(menubar, tearoff=0)
        self.newmenu.add_command(label='Closed Braid...',
                                 command=self.new_braid)
        self.newmenu.add_command(label='Knot...', command=self.new_knot)
        self.newmenu.add_command(label='XO link...', command=self.new_XO)
        filemenu.add_cascade(label='New', menu=self.newmenu)
        filemenu.add_command(label='Open File...', command=self.open)
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=self.root.destroy)
        menubar.add_cascade(label='File', menu=filemenu)
        self.windowmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Windows', menu=self.windowmenu)
        self.helpmenu = Menu(menubar, tearoff=0)
        self.helpmenu.add_command(label='About Gridlink...',
                                  command=self.about)
        self.helpmenu.add_command(label='Instructions...', command=self.help)
        menubar.add_cascade(label='Help', menu=self.helpmenu)
        self.root.config(menu=menubar)
        self.splash = PhotoImage(data=splash_string)
        canvas = Canvas(self.root, width=200, height=200)
        canvas.create_image(0, 0, anchor=NW, image=self.splash)
        canvas.pack()
        self.root.geometry('+%d+%d'%(100,25))
        self.root.resizable(False,False)
 
    def remove(self, gridlink):
        index = self.windows.index(gridlink)
        self.windowmenu.delete(index)
        self.windows.remove(gridlink)
        if len(self.windows) == 0:
            self.root.deiconify()

    def add(self, gridlink):
        if len(self.windows) == 0:
            self.root.withdraw()
        self.windows.append(gridlink)
        self.windowmenu.add_command(label=gridlink.window.title(),
                                    command=gridlink.window.tkraise)

    def new_knot(self):
        KnotDialog(self.root, self)

    def new_braid(self):
        BraidDialog(self.root, self)

    def new_XO(self):
        XODialog(self.root, self)
 
    def open(self):
        filename = askopenfilename(title='Load a Gridlink')
        if filename:
            file = open(filename)
            exec(file.read())
            file.close()
            Gridlink(self, gridlist,
                     title=os.path.splitext(os.path.basename(filename))[0],
                     moves=moves)

    def about(self):
        InfoDialog(self.root, 'About Gridlink', about_string%revision)

    def help(self):
        doc_file = 'gridlink.html'
        doc_file2 = os.path.join('gridlink', 'doc', doc_file)
        for path in sys.path + [os.path.abspath(os.path.dirname(sys.argv[0]))]:
            doc_path = os.path.join(path, doc_file)
            if os.path.exists(doc_path):
                break
            doc_path = os.path.join(path, doc_file2)
            if os.path.exists(doc_path):
                break
        doc_path = os.path.abspath(doc_path)
        url = 'file:' + pathname2url(doc_path)
        try:
            webbrowser.open(url) 
        except:
            showwarning('Not found!', 'Could not open URL\n(%s)'%url)

            
class Gridlink:
    """
    A Tkinter window in which one can perform basic moves on links
    composed of horizontal and vertical segments in general position.
    When two segments are highlighted in blue, click the mouse to
    exchange.  Click and drag the mouse on the background to do cyclic
    permutation.

    Initialize with a list of tuples, each specifying one component of
    the link.  To generate the tuples, order the horizontal and
    vertical segments of the entire link, from top to bottom and left
    to right, starting with 0 in each family.  Then, for each
    component, list the indices of its segments in order, starting
    with a horizontal segment.
    """
    def __init__(self, app, gridlist, unit=30, style='edges',
                 title='Gridlink', moves=[]):
        self.app = app
        self.gridlist = gridlist
        self.moves = moves
        self.components = len(gridlist)
        self.unit = unit
        self.style = style
        self.segments = []
        self.gridlines = []
        self.winding = []
        self.step = 0
        self.enabled = {}
        self.x = 0
        self.y = 0
        self.selected = None
        self.buddy = None
        self.set_size(gridlist)
        self.window = Toplevel(app.root)
        self.window.title(title)
        self.window.bind('<Key>', self.keypress)
        self.window.protocol('WM_DELETE_WINDOW', self.exit)
        self.show_grid = BooleanVar(self.window)
        self.show_winding = BooleanVar(self.window)
        self.show_TB = BooleanVar(self.window)
        self.show_XO = BooleanVar(self.window)
        self.XOpos = BooleanVar(self.window)
        menubar = Menu(self.window)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_cascade(label='New', menu=self.app.newmenu)
        filemenu.add_command(label='Open File...', command=self.app.open)
        filemenu.add_command(label='Save as...', command=self.save_as)
        filemenu.add_command(label='Snapshot...', command=self.snapshot)
        filemenu.add_separator()
        filemenu.add_command(label='Close', command=self.exit)
        menubar.add_cascade(label='File', menu=filemenu)
        viewmenu = Menu(menubar, tearoff=0)
        viewmenu.add_command(label='Edges',
                             command=lambda:self.set_style('edges'))
        viewmenu.add_command(label='Dots',
                             command=lambda:self.set_style('dots'))
        viewmenu.add_command(label="X's & O's",
                             command=lambda:self.set_style('XO'))
        viewmenu.add_checkbutton(label='Grid', variable=self.show_grid,
                                 command=self.set_grid)
        viewmenu.add_checkbutton(label='Winding', variable=self.show_winding,
                                 command=self.set_winding)
        viewmenu.add_checkbutton(label='T-B number', variable=self.show_TB,
                                 command=self.set_TB)
        viewmenu.add_checkbutton(label='X & O lists', variable=self.show_XO,
                                 command=self.set_XOlists)
        viewmenu.add_checkbutton(label='X & O > 0', variable=self.XOpos,
                                 command=self.drawknot)
        menubar.add_cascade(label='View', menu=viewmenu)
        movemenu = Menu(menubar, tearoff=0)
        movemenu.add_command(label='Reset', command=self.reset)
        movemenu.add_command(label='Review', command=self.review)
        movemenu.add_separator()
        movemenu.add_command(label='Simplify', command=self.simplify)
        menubar.add_cascade(label='Moves', menu=movemenu)
        if (TkHFK):
            invariantmenu = Menu(menubar, tearoff=0)
            invariantmenu.add_command(label='HFK^', command=self.HFKhat)
            menubar.add_cascade(label='Invariants', menu=invariantmenu)
        menubar.add_cascade(label='Windows', menu=self.app.windowmenu)
        menubar.add_cascade(label='Help', menu=self.app.helpmenu)
        self.window.config(menu=menubar)
        vscrollbar = AutoScrollbar(self.window)
        hscrollbar = AutoScrollbar(self.window, orient=HORIZONTAL)
        scrollsize = (self.size + 1)*self.unit
        self.canvas = Canvas(self.window, width=scrollsize, height=scrollsize,
                             background='white', borderwidth=4, relief=RIDGE,
                             yscrollcommand=vscrollbar.set,
                             xscrollcommand=hscrollbar.set)
        vscrollbar.config(command=self.canvas.yview)
        hscrollbar.config(command=self.canvas.xview)
        self.canvas.config(scrollregion = (0,0,scrollsize,scrollsize))
        self.canvas.bind('<Button-1>', self.mousedown)
        self.canvas.bind('<B1-Motion>', self.scroll)
        self.canvas.bind('<Motion>', self.select)

        self.frame = Frame(self.window, borderwidth=4, relief=RIDGE)
        self.frame.grid_columnconfigure(6, weight=1)
        button = Button(self.frame, text='Destab', command=self.destab_state,
                        underline=0)
        button.grid(row=0, column=0)
        self.NW_button = Button(self.frame, text='NW', command=self.NW_state)
        self.NW_button.grid(row=0, column=1)
        self.NE_button = Button(self.frame, text='NE', command=self.NE_state)
        self.NE_button.grid(row=0,column=2)
        self.SW_button = Button(self.frame, text='SW', command=self.SW_state)
        self.SW_button.grid(row=0, column=3)
        self.SE_button = Button(self.frame, text='SE', command=self.SE_state)
        self.SE_button.grid(row=0, column=4)
        button = Button(self.frame, text='Undo', command=self.undo,
                        underline=0)
        button.grid(row=0, column=5)
        self.showmoves = StringVar(self.window)
        moves = Label(self.frame, textvariable = self.showmoves, width=5,
                      background='white', borderwidth=2, relief=SUNKEN)
        moves.grid(row=0, column=6, sticky=W, padx=4, pady=4)
        self.rev_button = Button(self.frame, text='Reverse',
                         command=self.reverse_state, underline=0)
        self.rev_button.grid(row=0, column=7, sticky=W+E, padx=10)
        reflect = Button(self.frame, text='Reflect', command=self.reflect,
                        underline=2)
        reflect.grid(row=1, column=7, sticky=W+E, padx=10)
        self.enabled['NW'] = IntVar(self.window)
        check = Checkbutton(self.frame, variable=self.enabled['NW'],
                            command=self.NW_control)
        check.select()
        check.grid(row=1, column=1)
        self.enabled['NE'] = IntVar(self.window)
        check = Checkbutton(self.frame, variable=self.enabled['NE'],
                            command=self.NE_control)
        check.select()
        check.grid(row=1, column=2)
        self.enabled['SW'] = IntVar(self.window)
        check = Checkbutton(self.frame, variable=self.enabled['SW'],
                            command=self.SW_control)
        check.select()
        check.grid(row=1, column=3)
        self.enabled['SE'] = IntVar(self.window)
        check = Checkbutton(self.frame, variable=self.enabled['SE'],
                            command=self.SE_control)
        check.select()
        check.grid(row=1, column=4)

        self.XOentry = Entry(self.window, borderwidth=4, relief=RIDGE,
                             state="readonly")
        
        self.canvas.grid(row=0, column=0, sticky=E+W+N+S)
        vscrollbar.grid(row=0, column=1, sticky=N+S)
        hscrollbar.grid(row=1, column=0, sticky=E+W)
        self.XOentry.grid(row=2, column=0, columnspan=2, sticky=E+W+N+S, pady=0)
        self.frame.grid(row=3, column=0, columnspan=2, sticky=E+W+N+S,
                        padx=3, pady=1)
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.tk.call("grid", "remove", self.XOentry)

        self.build(gridlist)
        if len(self.moves) > 0:
            self.end()
        self.normal_state()
        self.zoom()
        self.app.add(self)
        
    def __repr__(self):
        repr = []
        for hseg in self.hlist:
            hseg.flag = 0
        for hseg in self.hlist:
            if hseg.flag == 1:
                continue
            component = []
            segment = hseg
            while 1:
                segment.flag = 1
                component.append(segment.level)
                segment = segment.next
                if segment == hseg:
                    break
            repr.append(component)
        return str(repr)

    def noop(self):
        pass
      
    def set_cursor(self, new_cursor):
        self.canvas.config(cursor=new_cursor)
        self.frame.config(cursor=new_cursor)

    def zoom(self):
        self.window.update_idletasks()
        height = min(self.window.winfo_screenheight() - 100,
                     self.window.winfo_height())
        width = min(self.window.winfo_screenwidth() - 100,
                    self.window.winfo_width())
        if (self.window.winfo_height() > height or
            self.window.winfo_width() > width):
            self.window.wm_geometry('%dx%d'%(width, height))

    def exit(self):
        self.window.destroy()
        self.app.remove(self)
        
    def set_size(self, gridlist):
        self.size = 0
        for component in gridlist:
            self.size += len(component)/2
        self.hlist = range(self.size)
        self.vlist = range(self.size)
        
    def build(self, gridlist):
        for component in gridlist:
            horizontal = True
            seglist = []
            for i in component:
                newsegment = Segment(i, horizontal, self.canvas,
                                     self.unit, self.style)
                seglist.append(newsegment)
                if horizontal:
                    self.hlist[i] = newsegment
                else:
                    self.vlist[i] = newsegment
                horizontal ^= True
            for i in range(len(seglist)):
                seglist[i-1].connect(seglist[i])
            self.segments += seglist
        
    def save_as(self):
        saveasfile = asksaveasfile(mode='w',
                                   title='Save Projection and Moves',
                                   filetypes=[('Any','*')])
        if saveasfile:
            if len(self.gridlist) == 0:
                saveasfile.write('X = []\nO=[]\ngridlist = []\n')
            else:
                X, O = self.get_XOlists()
                saveasfile.write('X = %s\n'%str(X).replace(', ',','))
                saveasfile.write('O = %s\n'%str(O).replace(', ',','))
                saveasfile.write('gridlist = [\n')
                for component in self.gridlist[:-1]:
                    saveasfile.write('  ' + str(component) + ',\n')
                saveasfile.write('  ' + str(self.gridlist[-1]) + ']\n')
            if len(self.moves) == 0:
                saveasfile.write('moves = []\n')
            else:
                saveasfile.write('moves = [\n')
                for move in self.moves[:-1]:
                    saveasfile.write('  ' + str(move) + ',\n')
                saveasfile.write('  ' + str(self.moves[-1]) + ']\n')
            saveasfile.close()

    def snapshot(self):
        psfile = asksaveasfile(mode='w',
                               title='Save as Postscript',
                               defaultextension='.eps',
                               filetypes=[('Postscript','*.eps'),
                                          ('Postscript','*.ps'),
                                          ('Any','*')])
        if psfile:
            psfile.write(self.canvas.postscript())
            psfile.close()

    def set_style(self, style):
        self.style = style
        for segment in self.segments:
            segment.set_style(style)
        self.drawknot()
        
    def set_grid(self):
        if self.show_grid.get():
            self.draw_gridlines()
        else:
            self.erase_gridlines()

    def set_winding(self):
        if self.show_winding.get():
            self.draw_winding()
        else:
            self.erase_winding()

    def set_TB(self):
        if self.show_TB.get():
            self.draw_TB()
        else:
            self.erase_TB()

    def set_XOlists(self):
        if self.show_XO.get():
            self.XOentry.grid()
        else:
            self.XOentry.config(state=NORMAL)
            self.XOentry.delete(0,END)
            self.XOentry.config(state="readonly")
            self.window.tk.call("grid", "remove", self.XOentry)
        self.drawknot()

    def reset(self):
        self.moves=[]
        self.gridlist = self.get_gridlist()
        self.drawknot()

    def review(self):
        self.step = len(self.moves)
        dialog = ReviewDialog(self.window, self)
        if self.step < len(self.moves):
            self.end()

    def forward(self, draw=True):
        if self.step < len(self.moves):
            self.apply(self.moves[self.step])
            self.step += 1
            if draw:
                self.set_scrollregion()
                self.drawknot()
        else:
            self.window.bell()

    def end(self):
        while self.step < len(self.moves) -1:
            self.forward(draw=False)
        self.forward()
    
    def backward(self, draw=True):
        if self.step > 0:
            self.inverse(self.moves[self.step - 1])
            self.step -= 1
            if draw:
                self.set_scrollregion()
                self.drawknot()
        else:
           self.window.bell()

    def start(self):
        while self.step > 1:
            self.backward(draw=False)
        self.backward()
            
    def normal_state(self):
        self.deselect()
        self.state = 'normal'
        self.set_cursor('exchange')
        self.set_scrollregion()
        self.drawknot()
        
    def reverse_state(self):
        if self.state =='reversing':
            self.normal_state()
            return
        self.deselect()
        self.state = 'reversing'
        self.set_cursor('double_arrow')
        
    def destab_state(self):
        if self.state =='destab':
            self.normal_state()
            return
        self.deselect()
        self.state = 'destab'
        self.set_cursor('pirate')
        
    def NW_state(self):
        if self.state =='NW':
            self.normal_state()
            return
        self.deselect()
        self.state = 'NW'
        self.set_cursor('ul_angle')
 
    def NW_control(self):
        if self.enabled['NW'].get():
            self.NW_button.config(state=NORMAL)
        else:
            self.NW_button.config(state=DISABLED)
            
    def NE_state(self):
        if self.state =='NE':
            self.normal_state()
            return
        self.deselect()
        self.state = 'NE'
        self.set_cursor('ur_angle')

    def NE_control(self):
        if self.enabled['NE'].get():
            self.NE_button.config(state=NORMAL)
        else:
            self.NE_button.config(state=DISABLED)

    def SW_state(self):
        if self.state =='SW':
            self.normal_state()
            return
        self.deselect()
        self.state = 'SW'
        self.set_cursor('ll_angle')

    def SW_control(self):
        if self.enabled['SW'].get():
            self.SW_button.config(state=NORMAL)
        else:
            self.SW_button.config(state=DISABLED)

    def SE_state(self):
        if self.state =='SE':
            self.normal_state()
            return
        self.state = 'SE'
        self.set_cursor('lr_angle')

    def SE_control(self):
        if self.enabled['SE'].get():
            self.SE_button.config(state=NORMAL)
        else:
            self.SE_button.config(state=DISABLED)

    def deselect(self):
        for segment in self.segments:
            segment.turn_off()
        self.selected = None
        self.buddy = None
        
    def set_scrollregion(self):
        scrollsize = (self.size + 1)*self.unit
        self.canvas.config(scrollregion = (0,0,scrollsize,scrollsize))

    def select(self, event):
        delta_x, delta_y = event.x - self.x, event.y - self.y
        self.x, self.y = event.x, event.y
        u = self.unit
        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))
        vindex = (x - u/2)/u
        hindex = (y - u/2)/u
        segment = hseg = vseg = None
        buddy = hbuddy = vbuddy = None
        if 0 <= hindex < self.size:
            hseg = self.hlist[hindex]
            x0 = (1 + hseg.prev.level)*u
            x1 = (1 + hseg.next.level)*u
            if min(x0,x1) + u/4 < x < max(x0,x1) - u/4:
                if y > (hseg.level + 1)*u:
                    hbuddy = self.hlist[(hindex+1)%self.size]
                else:
                    hbuddy = self.hlist[(hindex-1)%self.size]
        if 0 <= vindex < self.size:
            vseg = self.vlist[vindex]
            y0 = (1 + vseg.prev.level)*u
            y1 = (1 + vseg.next.level)*u
            if min(y0,y1) + u/4 < y < max(y0,y1) - u/4:
                if x > (vseg.level + 1)*u:
                    vbuddy = self.vlist[(vindex+1)%self.size]
                else:
                    vbuddy = self.vlist[(vindex-1)%self.size]
        if hbuddy and vbuddy:
            if delta_x > delta_y:
                segment, buddy = hseg, hbuddy
            else:
                segment, buddy = vseg, vbuddy
        elif hbuddy:
            segment, buddy = hseg, hbuddy
        elif vbuddy:
            segment, buddy = vseg, vbuddy
        if self.selected != segment or self.buddy != buddy:
            if self.selected:
                if self.state == 'normal':
                    self.selected.turn_off()
                    self.buddy.turn_off()
                elif self.state == 'reversing':
                    self.selected.turn_off_component()
                else:
                    self.selected.turn_off()
            if segment:
                if self.state == 'normal':
                    if self.legal(segment, buddy):
                        segment.turn_on()
                        buddy.turn_on()
                elif self.state == 'destab':
                    type = self.destab_type(segment)
                    if not type or not self.enabled[type].get():
                        return
                    segment.turn_on()
                elif self.state == 'reversing':
                    segment.turn_on_component()
                else:
                    segment.turn_on()
            self.selected, self.buddy = segment, buddy

    def mousedown(self, event):
        self.x, self.y = event.x, event.y
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasx(event.y)
        if self.selected:
            if self.state == 'normal':
                level = min(self.selected.level, self.buddy.level)
                if level == 0:
                    if max(self.selected.level, self.buddy.level) != 1:
                        level = self.size - 1
                if self.selected.horizontal:
                    self.exchange(level,'h')
                else:
                    self.exchange(level,'v')
            elif self.state == 'destab':
                self.destabilize(self.selected)
                self.normal_state()
            elif self.state == 'reversing':
                self.reverse_component(self.selected)
                self.normal_state()
            else:
                self.stabilize(self.selected, self.state)
                self.normal_state()

    def keypress(self, event):
        if event.char == 'd': self.destab_state()
        if event.char == 'f': self.reflect()
        if event.char == 'r': self.reverse_state()
        if event.char == 'u': self.undo()
        if event.keysym == 'Down' : self.roll(-1,0)
        if event.keysym == 'Up'   : self.roll(1,0)
        if event.keysym == 'Right': self.roll(0,-1)
        if event.keysym == 'Left' : self.roll(0,1)
        
    def drawknot(self):
        if self.selected:
            self.selected.turn_off()
            self.selected = None
        for segment in self.segments:
            segment.erase()
        for segment in self.hlist:
            segment.draw()
        for segment in self.vlist:
            segment.draw()
        if self.show_grid.get():
            self.erase_gridlines()
            self.draw_gridlines()
        if self.show_winding.get():
            self.erase_winding()
            self.draw_winding()
        if self.show_TB.get():
            self.erase_TB()
            self.draw_TB()
        if self.show_XO.get():
            X,O = self.get_XOlists()
            X,O = ','.join([str(x) for x in X]), ','.join([str(o) for o in O]) 
            text = "X=[%s];   O=[%s]"%(X,O)
            self.XOentry.config(state=NORMAL)
            self.XOentry.delete(0, END)
            self.XOentry.insert(END, text)
            self.XOentry.config(state="readonly")
        self.showmoves.set(str(len(self.moves)))

    def scroll(self, event):
        if not self.selected:
            u = self.unit/2
            h = (self.y - event.y)/u
            if h < 0:
                h += 1
            v = (self.x - event.x)/u
            if v < 0:
                v += 1
            if h or v:
                self.x, self.y = event.x, event.y
                self.roll(h, v)
            
    def exchange(self, i, type, beep=True, record=True, draw=True):
        if type == 'h':
            seglist = self.hlist
        elif type == 'v':
            seglist = self.vlist
        i = i % self.size
        j = (i+1) % self.size
        if self.legal(seglist[i], seglist[j]):
            temp = seglist[i]
            seglist[i] = seglist[j]
            seglist[j] = temp
            seglist[i].level = i
            seglist[j].level = j
            if record:
                self.moves.append(('exchange',type,i))
            if draw:
                self.drawknot()
        elif beep:
            self.window.bell()

    def legal(self, seg1, seg2):
        u0, u1 = seg1.prev.level, seg1.next.level
        v0, v1 = seg2.prev.level, seg2.next.level
        if min(u0,u1) < min(v0,v1) < max(u0,u1) < max(v0,v1):
            return 0
        if min(v0,v1) < min(u0,u1) < max(v0,v1) < max(u0,u1):
            return 0
        return 1

    def roll(self, h, v, record=True, draw=True):
        h = h%self.size
        v = v%self.size
        self.hlist = self.hlist[h:]+self.hlist[:h]
        self.vlist = self.vlist[v:]+self.vlist[:v]
        for i in range(self.size):
            self.hlist[i].level = i
            self.vlist[i].level = i
        if record:
            self.moves.append(('roll',h,v))
        if draw:
            self.drawknot()
            
    def reverse_component(self, segment):
        next = segment.next
        segment.reverse()
        while next != segment:
           next.reverse()
           next = next.prev

    def reflect(self):
        for seg in self.hlist + self.vlist:
            seg.reflect(self.size)
        self.hlist, self.vlist = self.vlist, self.hlist
        self.vlist.reverse()
        self.normal_state()
        self.reset()
        
    Opposite = {'E':'W', 'W':'E', 'N':'S', 'S':'N' }

    def destab_type(self, segment):
        if len(segment) != 1:
            return
        if segment.horizontal:
            dir = Gridlink.Opposite[segment.dir()]
            next_dir = segment.next.dir()
            if (segment.next.dir() != segment.prev.dir() and
                len(segment.next) > len(segment.prev)):
                next_dir = Gridlink.Opposite[next_dir]
            return next_dir + dir
        else:
            dir = segment.dir()
            next_dir = Gridlink.Opposite[segment.next.dir()]
            if (segment.next.dir() != segment.prev.dir() and
                len(segment.next) > len(segment.prev)):
                next_dir = Gridlink.Opposite[next_dir]
            return dir + next_dir

    Hshift = {'NW':0, 'NE':0, 'SW':1 , 'SE':1 }

    Vshift = {'NW':0, 'NE':1, 'SW':0 , 'SE':1 }
    
    def stabilize(self, segment, type, record=True):
        index = segment.level
        self.size += 1
        V = Segment(0, False, self.canvas, self.unit, self.style)
        H = Segment(0, True, self.canvas, self.unit, self.style)
        self.segments += [V,H]
        hs = Gridlink.Hshift[type]
        vs = Gridlink.Vshift[type]
        if segment.horizontal:
            segtype = 'h'
            H.connect(V)
            self.hlist.insert(segment.level + 1 - hs, H)
            self.vlist.insert(segment.prev.level + 1 - vs, V)
            segment.prev.connect(H)
            V.connect(segment)
        else:
            segtype = 'v'
            V.connect(H)
            self.hlist.insert(segment.prev.level + hs, H)
            self.vlist.insert(segment.level + vs, V)
            segment.prev.connect(V)
            H.connect(segment)
        for i in range(self.size):
            self.hlist[i].level = i
            self.vlist[i].level = i
        if record:
            self.moves.append(('stabilize', segtype, index, type)) 

    def destabilize(self, segment, record=True):
        type = self.destab_type(segment)
        sign = 1
        if len(segment) == 1 and segment.next.next != segment.prev.prev:
            seg = segment
            if  segment.prev.dir() == segment.next.dir():
                adjacent = segment.next
                remember = adjacent.next
                if adjacent.dir() in ('E','S'):
                    sign = -1
                seg.prev.next = adjacent.next
                adjacent.next.prev = seg.prev
            else:
                if len(segment.next) < len(segment.prev):
                    adjacent = segment.next
                    remember = adjacent.next
                    if adjacent.dir() in ('E','S'):
                        sign = -1
                    seg.prev.next = adjacent.next
                    adjacent.next.prev = seg.prev
                else:
                    adjacent = segment.prev
                    remember = segment.next
                    if adjacent.dir() in ('W','N'):
                        sign = -1
                    adjacent.prev.next = seg.next
                    seg.next.prev = adjacent.prev
            count = sign*(len(adjacent) - 1)
            exchanges = (segment.level - count, count)
            if segment.horizontal:
                exchanges = ('h',) + exchanges
            else:
                exchanges = ('v',) + exchanges
            index = remember.level
            seg.next = seg.prev = adjacent.next = adjacent.prev = None
            seg.erase()
            adjacent.erase()
            if seg.horizontal:
                self.hlist.remove(seg)
                self.vlist.remove(adjacent)
            else:
                self.hlist.remove(adjacent)
                self.vlist.remove(seg)
            self.segments.remove(seg)
            self.segments.remove(adjacent)
            self.size -= 1
            for i in range(self.size):
                self.hlist[i].level = i
                self.vlist[i].level = i
            if record:
                if remember.horizontal:
                    segtype = 'h'
                else:
                    segtype = 'v'
                self.moves.append(
                    ('destabilize', segtype, index, type, exchanges))
            return True
        return False

    def destabilize_any(self, excluded=[], beep=True, draw=True):
        for list in (self.hlist, self.vlist):
            for segment in list:
                if self.destab_type(segment) in excluded:
                    continue
                if self.destabilize(segment):
                    if draw:
                        self.set_scrollregion()
                        self.drawknot()
                    return True
        if beep:
            self.window.bell()
        return False
            
    def inverse(self, move):
        op = move[0]
        if op == 'roll':
            h,v = move[1:3]
            self.roll(-h, -v, record=False)
        segtype, index = move[1:3]
        if op == 'exchange':
            self.exchange(index, segtype, record=False)
        if op == 'stabilize':
            type = move[3]
            if segtype == 'h':
                segment = self.hlist[index+Gridlink.Hshift[type]]
            else:
                segment = self.vlist[index-Gridlink.Vshift[type]+1]
            self.destabilize(segment.prev, record=False)
        if op == 'destabilize':
            type, exchanges = move[3:5]
            if segtype == 'h':
                segment = self.hlist[index-Gridlink.Hshift[type]]
            else:
                segment = self.vlist[index+Gridlink.Vshift[type]-1]
            save = segment.prev
            self.stabilize(segment, type, record=False)
            segtype, index, count = exchanges
            if count > 0:
                for i in range(count):
                    self.exchange(index + i, segtype, record=False) 
            else:
                for i in range(-count):
                    self.exchange(index - i - 1, segtype, record=False)

    def apply(self, move):
        op = move[0]
        if op == 'roll':
            h,v = move[1:3]
            self.roll(h, v, record=False)
        segtype, index = move[1:3]
        if op == 'exchange':
            self.exchange(index, segtype, record=False)
        if op == 'stabilize':
            type = move[3]
            if segtype == 'h':
                segment = self.hlist[index]
            else:
                segment = self.vlist[index]
            self.stabilize(segment, type, record=False)
        if op == 'destabilize':
            type, exchanges = move[3:5]
            segtype, index, count = exchanges
            if segtype == 'h':
                segment = self.hlist[index + count]
            else:
                segment = self.vlist[index + count]
            self.destabilize(segment, record=False)

    def undo(self):
        try:
            move = self.moves.pop()
            self.inverse(move)
        except IndexError:
            self.window.bell()
        self.set_scrollregion()
        self.drawknot()

    def randomize(self, n=1, delay=0, draw=True):
        self.moves=[]
        while n > 0:
            if randint(0,1):
                dir = 'h'
            else:
                dir = 'v'
            if randint(0,1):
                strand = randint(0,self.size)
                self.exchange(strand, dir, False, False, draw)
            else:
                j, k = randint(0, self.size-1), randint(0, self.size-1)
                self.roll(j, k, False, draw)
            n -= 1
            if delay:
                self.window.after(delay, self.randomize, n, delay)
                break

    def randomize2(self, n=1, draw=False):
        """
        Experimental version that tries a few stabilizations.
        """
        self.moves=[]
        while n > 0:
            if randint(0,1):
                dir = 'h'
            else:
                dir = 'v'
            move = randint(0,5)
            if move < 2:
                strand = randint(0,self.size)
                self.exchange(strand, dir, False, False, draw)
            elif move < 4:
                j, k = randint(0, self.size), randint(0, self.size)
                self.roll(j, k, False, draw)
            else:
                type = ('NW','NE','SW','SE')[randint(0,3)]
                seg = randint(0, self.size)
                self.stabilize(self.hlist[randint(0,self.size-1)],
                               type, record=False)
            n -= 1
        self.normal_state()

    def simplify(self, iterates=10000):
        self.set_cursor('watch')
        self.window.update()
        excluded = []
        for type in ('NW','NE','SW','SE'):
            if self.enabled[type].get() == 0:
                excluded.append(type)
        while iterates:
            iterates -= 1
            self.randomize(draw=False)
            while self.destabilize_any(excluded=excluded, beep=False):
                pass
        self.set_scrollregion()
        self.normal_state()
        self.reset()

    def draw_gridlines(self):
        size = self.unit*self.size
        half = self.unit/2
        for n in range(self.size + 1):
            z = n*self.unit + half
            self.gridlines.append(self.canvas.create_line(
                        (z,half,z,half+size), width=1, fill='light gray'))
            self.gridlines.append(self.canvas.create_line(
                        (half,z,half + size,z), width=1, fill='light gray'))

    def erase_gridlines(self):
        for line in self.gridlines:
            self.canvas.delete(line)
        self.gridlines = []

    def draw_winding(self):
        W = self.winding_numbers()
        half = self.unit/2
        for i in range(self.size):
            for j in range(self.size):
                self.winding.append(
                    self.canvas.create_text(
                    (j*self.unit+half+1, (i+1)*self.unit+half),
                    text=str(W[i][j]), anchor=SW, fill='dark blue'))

    def erase_winding(self):
        for number in self.winding:
            self.canvas.delete(number)
        self.winding = []
        
    def draw_TB(self):
        self.TB = self.canvas.create_text(
            (self.unit/2, self.unit/2), anchor=SW, fill="#8b008b",
            text='tb =  %d ;  rotation = %r '%(self.tb(), self.rotation()))

    def erase_TB(self):
        self.canvas.delete(self.TB)
            
    def print_moves(self):
        for move in self.moves:
            print '\t'.join([str(x) for x in move])

    def get_gridlist(self):
        gridlist = []
        H = [segment for segment in self.hlist]
        V = [segment for segment in self.vlist]
        while len(H) > 0:
            nexth = first = H[0]
            component = []
            while True:
                component.append(nexth.level)
                H.remove(nexth)
                nextv = nexth.next
                component.append(nextv.level)
                nexth = nextv.next
                if nexth == first:
                    break
            gridlist.append(component)
        return gridlist

    def get_XOlists(self, force_zero=False):
        """
        Return lists X and O.
        X[i] (O[i]) is the y coordinate of the X (O) vertex in column i.
        THE BOTTOM OF THE DIAGRAM HAS Y-COORDINATE 0.
        """
        X = []
        O = []
        for segment in self.vlist:
            X.append(self.size - 1 - segment.prev.level)
            O.append(self.size - 1 - segment.next.level)
        if self.XOpos.get() and not force_zero:
            X = [x+1 for x in X]
            O = [o+1 for o in O]
        return X, O
    
    def HFKhat(self):
        if self.components > 1:
            showwarning('Knots only',
                        'Sorry, I can only compute HFK^ for knots.')
            return
        Xlist, Olist = self.get_XOlists(force_zero=True)
        hfk_object = TkHFK(Xlist, Olist, name=self.window.title())
        hfk_object.HFK_ranks()

    def winding_numbers(self):
        result = []
        for i in range(self.size):
            row = [0]
            for j in range(self.size):
                tail = self.vlist[j].prev.level
                head = self.vlist[j].next.level
                if tail <= i < head:
                    row.append(row[-1] + 1)
                elif head <= i < tail:
                    row.append(row[-1] - 1)
                else:
                    row.append(row[-1])
            result.append(row)
        return result

    def Alexander_shift(self):
        """
        This follows the convention used by Baldwin and Gillam.
        """
        X = [seg.next.level for seg in self.vlist]
        O = [seg.prev.level for seg in self.vlist]
        X.append(X[0])
        O.append(O[0])
        WN = self.winding_numbers()
        for row in WN:
            row.append(row[0])
        S = 0
        for i in range(self.size):
            S += WN[X[i]][i]
            S += WN[X[i]-1][i];
            S += WN[X[i]][i+1];
            S += WN[X[i]-1][i+1];
            S += WN[O[i]][i]
            S += WN[O[i]-1][i];
            S += WN[O[i]][i+1];
            S += WN[O[i]-1][i+1];
        shift = (S - 4 * self.size + 4)/8;
        return shift

    def writhe(self):
        """
        Compute the writhe of the diagram.
        """
        positive = 0
        negative = 0
        for V in self.vlist:
            for H in self.hlist:
                #down
                if V.prev.level < H.level < V.next.level:
                    if H.prev.level < V.level < H.next.level:
                        positive += 1
                    elif H.prev.level > V.level > H.next.level:
                        negative += 1
                #up
                if V.prev.level > H.level > V.next.level:
                    if H.prev.level < V.level < H.next.level:
                        negative += 1
                    elif H.prev.level > V.level > H.next.level:
                        positive += 1
        return positive - negative

    def rotation(self):
        """
        Compute the rotation number of the diagram.
        """
        r = 0
        for V in self.vlist:
            if V.prev.dir() == 'W' and V.dir() == 'S': r += 1
            if V.dir() == 'S' and V.next.dir() == 'W': r += 1
            if V.prev.dir() == 'E' and V.dir() == 'N': r -= 1
            if V.dir() == 'N' and V.next.dir() == 'E': r -= 1
        return r/2

    def tb(self):
        """
        Compute the Thurston-Bennequin number of the diagram.
        """
        southeast = 0
        for V in self.vlist:
            if ((V.dir() == 'S' and V.next.dir() == 'W') or
                (V.dir() == 'N' and V.prev.dir() == 'E')):
                    southeast += 1
        return self.writhe() - southeast
                
class Segment:

    def __init__(self, level, horizontal, canvas, unit, style):
        self.level = level
        self.horizontal = horizontal
        self.canvas = canvas
        self.unit = unit
        self.style = style
        self.next = None
        self.prev = None
        self.flag = 0
        self.line = None
        self.X = None
        self.O = None
        self.highlight = None
        self.rectangle = None

    def __len__(self):
        return abs(self.next.level - self.prev.level)

    def dir(self):
        if self.horizontal:
            if self.prev.level < self.next.level:
                return 'E'
            else:
                return 'W'
        else:
            if self.prev.level < self.next.level:
                return 'S'
            else:
                return 'N'
            
    def connect(self, other):
        self.next = other
        other.prev = self

    def reverse(self):
        save = self.next
        self.next = self.prev
        self.prev = save
        
    def reflect(self, size):
        if self.horizontal:
            self.level = size - self.level - 1
        self.horizontal ^= 1
        
    def draw(self, highlight=0):
        if self.horizontal:
            x0 = (1 + self.prev.level)*self.unit
            x1 = (1 + self.next.level)*self.unit
            y  = (1 + self.level)*self.unit
            if highlight:
                self.highlight = self.canvas.create_line(
                  (x0,y,x1,y), width=2, fill='blue')
            else:
                if self.style == 'edges':
                    self.line = self.canvas.create_line(
                        (x0,y,x1,y), width=2, fill='red')
        else:
            y0 = (1 + self.prev.level)*self.unit
            y1 = (1 + self.next.level)*self.unit
            x  = (1 + self.level)*self.unit
            if highlight:
              self.highlight = self.canvas.create_line(
                  (x,y0,x,y1), width=2, fill='blue')
            else:
                if self.style == 'edges':
                    self.rectangle = self.canvas.create_rectangle(
                        (x-4, min(y0,y1)+4, x+4, max(y0,y1)-4),
                        fill='white', outline='')
                    self.line = self.canvas.create_line(
                        (x,y0,x,y1), width=2, fill='red', arrow='last')
                if self.style == 'dots':
                    self.X = self.canvas.create_oval((x-6,y0-6,x+6,y0+6),
                                                     width=2, fill='black')
                    self.O = self.canvas.create_oval((x-6,y1-6,x+6,y1+6),
                                                     width=2, fill='white')
                if self.style == 'XO':
                    self.X = self.canvas.create_text((x,y0), text='X',
                                           font='Helvetica 18 bold')
                    self.O = self.canvas.create_text((x,y1), text='O',
                                           font='Helvetica 18 bold')

    styles = ('edges', 'dots', 'XO')

    def set_style(self, style):
        if style in Segment.styles:
            self.style = style
            
    def erase(self):
        if self.highlight:
            self.canvas.delete(self.highlight)
        if self.line:
            self.canvas.delete(self.line)
        if self.X:
            self.canvas.delete(self.X)
        if self.O:
            self.canvas.delete(self.O)
        if self.rectangle:
            self.canvas.delete(self.rectangle)
        self.highlight = self.line = self.rectangle = None

    def turn_on(self):
        self.draw(highlight=1)

    def turn_off(self):
        self.canvas.delete(self.highlight)
    
    def turn_on_component(self):
        next = self
        while True:
            next.turn_on()
            next = next.next
            if next == self:
                break

    def turn_off_component(self):
        next = self
        while True:
            next.turn_off()
            next = next.next
            if next == self:
                break
        
class Unknot(Gridlink):
    """
    An unknot on an nxn grid.  Instantiate as Unknot(n).
    """
    
    def __init__(self, app, n):
        gridlist = range(2*n)
        for i in gridlist:
            gridlist[i] = i/2
        Gridlink.__init__(self, app, [gridlist])
        
    def __repr__(self):
       return 'unknot of size %d'%self.size

class ClosedBraid(Gridlink):
    """
    A gridlink representation of a closed braid.
    """
    def __init__(self, app, strands, word=None, unit=30, title=None):
        self.strands = strands
        self.matrix = [[1]*self.strands]
        self.indices = range(self.strands)
        self.size = self.strands
        if word:
            for x in word:
                self.twist(x)
        self.close()
        if title == None:
            title = '%d-Braid %s'%(strands, str(word))
        Gridlink.__init__(self, app, self.braid_to_gridlist(),
                          unit=unit, title=title)

    def __repr__(self):
        return self.diagram()
    
    def diagram(self):
        result = ''
        for row in self.matrix:
            for entry in row:
                if entry:
                    result += '*'
                else:
                    result += '.'
            result += '\n'
        return result

    def twist(self, k):
        """
        Switch strands |k|-1 and |k|.
        Positive sign means to cross strand k over strand k-1.
        Strands are numbered from 0.
        """
        if k == 0 or abs(k) >= self.strands:
            raise ValueError, 'Invalid strand index'
        if k < 0:
            k = -k
            self.size += 1
            for row in self.matrix:
                row.insert(self.indices[k-1],0)
            self.matrix.append([0]*self.size)
            self.matrix[-1][self.indices[k]+1] = 1
            for i in range(k+1, self.strands):
                self.indices[i] += 1
            self.indices[k] = self.indices[k-1] + 1
            self.matrix[-1][self.indices[k-1]] = 1
        elif k > 0:
            self.size += 1
            for row in self.matrix:
                row.insert(self.indices[k]+1,0)
            self.matrix.append([0]*self.size)
            self.matrix[-1][self.indices[k-1]] = 1
            self.indices[k-1] = self.indices[k]
            for i in range(k,self.strands):
                self.indices[i] += 1
            self.matrix[-1][self.indices[k]] = 1

    def close(self):
        start = self.matrix.pop(0)
        n = start.index(1)
        bottom = [[0]*self.size for i in range(self.strands)]

        #connect each non-trivial strand back to its start
        j = k = 0
        for i in range(self.strands):
            j = len([x for x in self.indices[i+1:] if x < n]) 
            bottom[k+j][n] = 1
            bottom[k+j][self.indices[i]] = 1
            if j == 0:
                k = i+1
            try:
                n = start.index(1,n+1)
            except ValueError:
                break
        self.matrix += bottom
        # Now deal with the trivial strands
        k = 0
        while k < self.size:
            if 1 == sum([self.matrix[j][k] for j in range(self.size)]):
                for row in self.matrix:
                    row.insert(k,0)
                self.size += 1
                self.matrix[k][k] = 1
                self.matrix.insert(0,[0]*self.size)
                self.matrix[0][k] = 1
                self.matrix[0][k+1] = 1
                for i in range(k,self.strands):
                    self.indices[i] += 1
                k += 2
            else:
                k += 1
        
    def braid_to_gridlist(self):
        dots = []
        gridlist = []
        for row in self.matrix:
            first = row.index(1)
            second = row.index(1, first+1)
            dots.append([first, second])
        while True:
            index = -1
            component = []
            for dot in dots:
                if dot:
                    index = dots.index(dot)
                    break
            if index == -1:
                break
            dot = dots[index]
            while True:
                if not dot:
                    break
                x = dot.pop()
                component.append(index)
                component.append(x)
                for next in dots:
                   if x in next:
                       index = dots.index(next)
                       next.remove(x)
                       dot = next
                       break
            gridlist.append(component)
        return gridlist

Bad_Knot_name = 'Example knot names:  9_12 11a_123 12n_1123'

class Knot(ClosedBraid):
    """
    A gridlink representation of a knot with up to 12 crossings.
    The knot name should look like 9_12 or 11n_123 or 12a_123.
    """
    def __init__(self, app, name, unit=30):
        try:
            braid = knot_dict[name]
        except:
            raise Bad_Knot_name 
        strands = max([abs(x) for x in braid]) + 1
        title = 'Knot ' + name
        ClosedBraid.__init__(self, app, strands, braid, unit=unit, title=title)

class XOlink(Gridlink):
    """
    A gridlink representation specified by a matrix with one X and one O
    in each row and column.  Vertical segments are oriented from X to O,
    horizontal segments from O to X.  Initialize with two lists, one
    containing the row indices of X's, the other containing row indices
    of the O's.  THE ROWS ARE ORDERED BOTTOM TO TOP.
    """
    def __init__(self, app, Xlist, Olist, unit=30):
        gridlist = []
        size = len(Xlist)
        rows = range(size)
        while len(rows) > 0:
            O = rows.pop(0)
            component = [size - 1 - O]
            while True:
                X = Xlist.index(O)
                component.append(X)
                O = Olist[X]
                if O not in rows:
                    break
                component.append(size - 1 - O)
                rows.remove(O)
            gridlist.append(component)
        title = ('X=' + str(Xlist).replace(' ','') +
                 ' O=' + str(Olist).replace(' ',''))
        Gridlink.__init__(self, app, gridlist, unit=unit, title=title)

class GridlinkDialog(tkSimpleDialog.Dialog):

    def __init__(self, parent, app=None, title='Gridlink'):
        self.app = app
        Toplevel.__init__(self, parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        self.buttonbox()
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.geometry('+%d+%d'%
           (parent.winfo_rootx()+parent.winfo_width()-100,
            parent.winfo_rooty()))
        self.initial_focus.focus_set()
        self.wait_window(self)

    def buttonbox(self):
        box = Frame(self)
        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

class InfoDialog(GridlinkDialog):
    def __init__(self, parent, title, content=''):
        self.parent = parent
        self.content = content
        Toplevel.__init__(self, parent)
        if title:
            self.title(title)
        self.icon = PhotoImage(data=icon_string)
        canvas = Canvas(self, width=58, height=58)
        canvas.create_image(10, 10, anchor=NW, image=self.icon)
        canvas.grid(row=0, column=0, sticky=N+W)
        text = Text(self, font='Helvetica 14',
                    width=50, height=16, padx=10)
        text.insert(END, self.content)
        text.grid(row=0, column=1, sticky=N+W, padx=10, pady=10)
        text.config(state=DISABLED)
        self.buttonbox()
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.ok)
        self.focus_set()
        self.wait_window(self)

    def buttonbox(self):
        box = Frame(self)
        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.ok)
        box.grid(row=1, columnspan=2)

    def ok(self, event=None):
        self.parent.focus_set()
        self.app = None
        self.destroy()

class ReviewDialog(GridlinkDialog):
    
    def __init__(self, parent, gridlink, title='Review Moves'):
        self.gridlink = gridlink
        GridlinkDialog.__init__(self, parent, title)
        
    def body(self, parent):
        self.step = StringVar(parent)
        self.step.set(str(self.gridlink.step))
        start_button = Button(parent, text='<<', command=self.start)
        back_button = Button(parent, text='<', command=self.back)
        step = Label(parent, textvariable = self.step,
                     width=5,background='white', borderwidth=2, relief=SUNKEN)
        fwd_button = Button(parent, text='>', command=self.forward)
        end_button = Button(parent, text='>>', command=self.end)

        start_button.grid(row=0, column=1)
        back_button.grid(row=0, column=2)
        step.grid(row=0, column=3)
        fwd_button.grid(row=0, column=4)
        end_button.grid(row=0, column=5)
       
    def buttonbox(self):
        box = Frame(self)
        w = Button(box, text='done', width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)
        self.bind('<Return>', self.cancel)
        self.bind('<Left>', lambda ev: self.back())
        self.bind('<Right>', lambda ev: self.forward())
        box.pack()
        
    def cancel(self, event=None):
        self.parent.focus_set()
        self.app = None
        self.destroy()

    def start(self):
        self.gridlink.start()
        self.step.set(str(self.gridlink.step))

    def forward(self):
        self.gridlink.forward()
        self.step.set(str(self.gridlink.step))

    def back(self):
        self.gridlink.backward()
        self.step.set(str(self.gridlink.step))

    def end(self):
        self.gridlink.end()
        self.step.set(str(self.gridlink.step))

class BraidDialog(GridlinkDialog):

    def body(self, parent):
        Label(parent, text='Strands: ').grid(row=0, column=0, sticky=E)
        if TkVersion > 8.399:
            self.strands = Spinbox(parent, width=2, from_=1, to=25)
        else:
            self.strands = Entry(parent, width=2)
        self.strands.grid(row=0, column=1, sticky=W, pady=4)
        Label(parent, text='Word: ').grid(row=1, column=0, sticky=E)
        self.word = Entry(parent, width=30)
        self.word.grid(row=1, column=1, sticky=W, pady=4)

    def validate(self):
        try:
            self.wordlist = [int(x) for x in self.word.get().split(',')]
            self.numstrands = int(self.strands.get())
            if max([abs(x) for x in self.wordlist]) >= self.numstrands:
                raise(ValueError)
        except:
            showwarning('No such braid', 'Invalid braid word')
            return 0
        return 1

    def apply(self):
        ClosedBraid(self.app, self.numstrands, self.wordlist)

class KnotDialog(GridlinkDialog):

    knot_counts = {'3':1, '4':1, '5':2, '6':3, '7':7, '8':21, '9':49,
                   '10':165, '11a':367, '11n':185, '12a':1288, '12n':888}
    def body(self, parent):
        Label(parent, text='Crossings: ').grid(row=0, column=0, sticky=E)
        self.crossings = StringVar(parent)
        self.crossings.set('3')
        option = OptionMenu(parent, self.crossings,
                            '3','4','5','6','7','8','9','10',
                            '11a','11n','12a','12n')
        option.grid(row=0, column=1, sticky=W+E, pady=4)
        Label(parent, text='Index: ').grid(row=1, column=0, sticky=E)
        self.index = Entry(parent, width=10)
        self.index.grid(row=1, column=1, sticky=W, pady=4)

    def validate(self):
        crossings = self.crossings.get()
        max = KnotDialog.knot_counts[crossings]
        try:
            index = int(self.index.get())
            if index < 1 or index > max:
                raise ValueError
        except:
            if crossings[-1] == 'a':
                msg = 'There are only %d alternating knots with %s crossings.'%(
                    max, crossings[:-1])
            elif crossings[-1] == 'n':
                msg = 'There are only %d non-alternating knots with %s crossings.'%(
                    max, crossings[:-1])
            elif max > 1:
                msg = 'There are only %d knots with %s crossings.'%(
                    max, crossings)
            else:
                msg = 'There is only %d knot with %s crossings.'%(
                    max, crossings)
            showwarning('No such knot', msg)
            return 0
        self.result = crossings + '_' + self.index.get()
        return 1

    def apply(self):
        Knot(self.app, self.result)
        
class XODialog(GridlinkDialog):

    def body(self, parent):
        Label(parent, text='X-permutation: ').grid(row=0, column=0, sticky=E)
        self.Xperm = Entry(parent, width=30)
        self.Xperm.grid(row=0, column=1, sticky=W, pady=4)
        Label(parent, text='O-permutation: ').grid(row=1, column=0, sticky=E)
        self.Operm = Entry(parent, width=30)
        self.Operm.grid(row=1, column=1, sticky=W, pady=4)

    def validate(self):
        try:
            self.Xlist = [int(x) for x in self.Xperm.get().split(',')]
            self.Olist = [int(x) for x in self.Operm.get().split(',')]
        except:
            showwarning('Invalid entry')
            return 0
        if len(self.Xlist) != len(self.Olist):
            showwarning('The permutations must be the same size')
            return 0
        if min(self.Xlist) == 1 and min(self.Olist) == 1:
            self.Xlist = [x-1 for x in self.Xlist]
            self.Olist = [o-1 for o in self.Olist]
        for i in range(len(self.Xlist)):
            if i not in self.Xlist or i not in self.Olist:
                showwarning('You must enter permutations')
                return 0
            if self.Xlist[i] == self.Olist[i]:
                showwarning('Degenerate components are not allowed')
                return 0
        return 1

    def apply(self):
        XOlink(self.app, self.Xlist, self.Olist)

class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    # Written by Frederik Lundh
    # http://effbot.org/zone/tkinter-autoscrollbar.htm 
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"

if __name__ == '__main__':
    App = GridlinkApp()
    try:
        App.root.tk.call('console','hide')
    except:
        pass
    App.root.focus()
    App.root.mainloop()
