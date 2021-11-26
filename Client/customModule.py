from npyscreen import wgwidget  as widget
from npyscreen import wgtextbox as textbox
import curses
import copy
import os

DIRECTORY = os.path.dirname(os.path.abspath(__file__)) 
logfile   = os.path.join(DIRECTORY, 'log.txt')

class MultiLine(widget.Widget):
    """Display a list of items to the user.  By overloading the display_value method, this widget can be made to 
display different kinds of objects.  Given the standard definition, 
the same effect can be achieved by altering the __str__() method of displayed objects"""
    _MINIMUM_HEIGHT = 2 # Raise an error if not given this.
    _contained_widgets = textbox.Textfield
    _contained_widget_height = 1
    def __init__(self, screen, values = None, value = None,
            widgets_inherit_color = False,
            always_show_cursor = False,
             **keywords):
        
        self.widgets_inherit_color = widgets_inherit_color
        self.clearLogFile()
        super(MultiLine, self).__init__(screen, **keywords)
        if self.height < self.__class__._MINIMUM_HEIGHT:
            raise widget.NotEnoughSpaceForWidget("Height of %s allocated. Not enough space allowed for %s" % (self.height, str(self)))
        self.make_contained_widgets()

        self.value = value
        
        self.always_show_cursor = always_show_cursor

        self.start_display_at = 0
        self.cursor_line = 0
        self.values = values or []
        
        #These are just to do some optimisation tricks
        self._total_lines = 0
        self._total_pages = 0 
        self._current_page= 0
        self._last_start_display_at = None
        self._last_cursor_line = None
        self._last_values = copy.copy(values)
        self._last_value = copy.copy(value)
    
    def resize(self):
        super(MultiLine, self).resize()
        self.make_contained_widgets()
        self.reset_display_cache()
        self.display()
    
    def make_contained_widgets(self, ):
        self._my_widgets = []
        for h in range(self.height // self.__class__._contained_widget_height):
            self._my_widgets.append(
                    self._contained_widgets(self.parent, 
                        rely=(h*self._contained_widget_height)+self.rely, 
                        relx = self.relx, 
                        max_width=self.width, 
                        max_height=self.__class__._contained_widget_height
                    )
                )


    def display_value(self, vl):
        """Overload this function to change how values are displayed.  
Should accept one argument (the object to be represented), and return a string or the 
object to be passed to the contained widget."""
        try:
            return self.safe_string(str(vl))
        except ReferenceError:
            return "**REFERENCE ERROR**"
        
        try:
            return "Error displaying " + self.safe_string(repr(vl))
        except:
            return "**** Error ****"

    def reset_cursor(self):
        self.start_display_at = 0
        self.cursor_line      = 0
    
    def reset_display_cache(self):
        self._last_values = False
        self._last_value  = False
    
    def update(self, clear=True):
        if self.hidden and clear:
            self.clear()
            return False
        elif self.hidden:
            return False
            
        if self.values == None:
            self.values = []
            
        display_length = len(self._my_widgets)

        if self.editing or self.always_show_cursor:
            if self.cursor_line < 0: self.cursor_line = 0
            if self.cursor_line > len(self.values)-1: self.cursor_line = len(self.values)-1
        
        # What this next bit does is to not bother updating the screen if nothing has changed.
        no_change = False

        if clear:
            no_change = False
        if not no_change or clear or self.never_cache:
            if clear is True: 
                self.clear()

            if (self._last_start_display_at != self.start_display_at) \
                    and clear is None:
                self.clear()
            else:
                pass

            self._last_start_display_at = self.start_display_at
            
            indexer = 0 + self.start_display_at
            for line in self._my_widgets[:-1]:
                self._print_line(line, indexer)
                line.task = "PRINTLINE"
                line.update(clear=True)
                indexer += 1
        
            # Now do the final line
            line = self._my_widgets[-1]
            
            if (len(self.values) <= indexer+1):# or (len(self._my_widgets)*self._contained_widget_height)<self.height:
                self._print_line(line, indexer)
                line.update(clear=False)
            elif len((self._my_widgets)*self._contained_widget_height)<self.height:
                self._print_line(line, indexer)
                line.update(clear=False)

            if self.editing or self.always_show_cursor: 
                self.set_is_line_cursor(self._my_widgets[(self.cursor_line-self.start_display_at)], True)
                self._my_widgets[(self.cursor_line-self.start_display_at)].update(clear=True)
            else:
                # There is a bug somewhere that affects the first line.  This cures it.
                # Without this line, the first line inherits the color of the form when not editing. Not clear why.
                self._my_widgets[0].update()


                
        self._last_start_display_at = self.start_display_at
        self._last_cursor_line = self.cursor_line
        self._last_values = copy.copy(self.values)
        self._last_value  = copy.copy(self.value)

    def _print_line(self, line, value_indexer):
        if self.widgets_inherit_color and self.do_colors():
            line.color = self.color
        self._set_line_values(line, value_indexer)
        self._set_line_highlighting(line, value_indexer)

    def _set_line_values(self, line, value_indexer):
        try:
            _vl = self.values[value_indexer]
        except IndexError:
            self._set_line_blank(line)
            return False
        except TypeError:
            self._set_line_blank(line)
            return False
        line.value = self.display_value(_vl)
        line.hidden = False
        
    def _set_line_blank(self, line):
        line.value    = None
        line.show_bold= False
        line.name     = None
        line.hidden   = True
        
    def _set_line_highlighting(self, line, value_indexer):
        if (value_indexer == self.value) and \
            (self.value is not None):
            self.set_is_line_bold(line, True)
        else: 
            self.set_is_line_bold(line, False)
        self.set_is_line_cursor(line, False)
        
    def set_is_line_bold(self, line, value):
        line.show_bold = value
    
    def set_is_line_cursor(self, line, value):
        line.highlight = value

    def set_up_handlers(self):
        super(MultiLine, self).set_up_handlers()
        self.handlers.update ( {
                    curses.KEY_UP:      self.h_cursor_line_up,
                    curses.KEY_DOWN:    self.h_cursor_line_down,
                    ord('k'):           self.h_cursor_line_up,
                    ord('j'):           self.h_cursor_line_down,
                    curses.ascii.TAB:   self.h_exit_down,
                } )

    def clearValues(self):
        self.values.clear()
        self.update(clear=True)

    def clearLogFile(self, *args):
        with open(logfile, 'r+') as file:
            file.truncate(0)

    def writeLogFile(self, message, *args):
        with open(logfile, 'a') as file:
            file.write(f'{message}\n')

    def screen_page_up(self):
        self.clearValues()
        with open(logfile, 'r') as file:
            for index, line in enumerate(file):
                if index >= self.height * (self._current_page - 1) and index <= (self.height * self._current_page) - 1:
                    self.values.append(line)
        self._current_page -= 1
        self.cursor_line = self.height - 1
        self.update(clear=True)

    def screen_page_down(self):
        self.clearValues()
        with open(logfile, 'r') as file:
            for index, line in enumerate(file):
                try:
                    if index >= (self._current_page + 1) * self.height and index <= ((self._current_page + 2) * self.height - 1):
                        self.values.append(line)
                except:
                    pass
        self._current_page += 1
        self.cursor_line = 0
        self.update(clear=True)

    def h_cursor_line_up(self, ch):
        if self.cursor_line == 0:
            if self._current_page != 0:
                self.screen_page_up()
        else:
            self.cursor_line -= 1

    def h_cursor_line_down(self, ch):
        if self.cursor_line + 1 == self.height / self._contained_widget_height:
            if self._current_page < self._total_pages:
                self.screen_page_down()
        else:
            self.cursor_line += 1

    def edit(self):
        self.editing = True
        self.how_exited = None
        self.display()
        while self.editing:
            self.get_and_use_key_press()
            self.update(clear=None)
            self.parent.refresh()

