import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from configparser import ConfigParser
import random
import os
import highscore as hs

VERSION = '1.0.0 beta'


class MinesweePy():

    def __init__(self, master):
        self.ini = ConfigParser()
        self.ini.read('config.ini')

        self.master = master
        self.running = False
        self.tk_mine_counter = None
        self.timer = None
        self.timer_handler_id = None
        self.gameover_handler = None

        self.load_theme(self.ini.get('settings', 'theme'))
        self.set_difficulty(self.ini.get('settings', 'difficulty'), False)

    def load_theme(self, theme):

        # self.img_blank = tk.PhotoImage(
        #     file=os.path.join('images', 'theme', 'blank.gif')
        # )
        self.img_covered = tk.PhotoImage(
            file=os.path.join('images', theme, 'field_covered.gif')
        )
        self.img_discovered = tk.PhotoImage(
            file=os.path.join('images', theme, 'field_discovered.gif')
        )
        self.img_covered_flag = tk.PhotoImage(
            file=os.path.join('images', theme, 'flag.gif')
        )
        self.img_mine = tk.PhotoImage(
            file=os.path.join('images', theme, 'mine.gif')
        )

        numbercolors = self.ini.items('numbercolors')
        self.numbercolors = {}
        for n in numbercolors:
            self.numbercolors[n[0]] = n[1]

    def game_over(self, win=False):
        timer.stop()
        self.running = False
        if not win:
            self.show_all_mines()
        if self.gameover_handler is not None:
            self.gameover_handler(self, win)

    def reset(self):
        self.running = False
        if self.timer is not None:
            self.timer.stop()
            self.timer.reset()
        self.new()

    def new(self):
        # reset mine counter
        self.update_minecounter(reset=True)

        # reset covered field counter
        self.covered_fields = self.width * self.height

        # clear the frame
        for widget in self.master.winfo_children():
            widget.destroy()

        # calculate mine positions
        mines = []
        mine_count = self.mine_count
        while mine_count > 0:
            mine_pos = str(
                    random.randint(0, self.width-1)
                ) + ':' + str(
                    random.randint(0, self.height-1)
                )
            if mine_pos not in mines:
                mines.append(mine_pos)
                mine_count -= 1

        # build field
        self.field = []
        for x in range(self.width):
            self.field.append([])
            for y in range(self.height):
                # create button-widget
                tile = tk.Button(
                    self.master, image=self.img_covered,
                    width=18, height=18, border=0, bd=0, relief=tk.FLAT,
                    padx=0, pady=0,
                    command=lambda *args, x=x, y=y: self.sec_discover(
                        args, x=x, y=y
                    )
                )
                tile.bind(
                    '<Button-3>', lambda e, x=x, y=y: self.toggle_lock(x, y)
                )
                tile.grid(column=x, row=y)

                # calculate numbers
                number = 0
                for neighbor_x in range(x-1, x+2):
                    if neighbor_x in range(0, self.width):
                        for neighbor_y in range(y-1, y+2):
                            if (
                                neighbor_y in range(0, self.height) and not
                                (neighbor_x == x and neighbor_y == y) and
                                self.str_mine_coord(
                                    neighbor_x, neighbor_y) in mines
                            ):
                                number += 1

                # assemble field-info-dict
                self.field[x].append({
                    'widget': tile,
                    'mine': (str(x) + ':' + str(y)) in mines,
                    'number': number,
                    'locked': False,
                    'discovered': False
                })

    def sec_discover(self, *args, x, y):
        """
        Security function to prevent an exception/missbehavior
        Tkinter sometimes executes the calling lambda function,
        which produces an error and sometimes strange missbehaviors, like
        dicovering/flagging new generated fields after a "game over"
        """
        if len(args[0]) == 0:
            self.discover(x, y)

    def str_mine_coord(self, x, y):
        return str(x) + ':' + str(y)

    def show_all_mines(self):
        for tiles_x in self.field:
            for tile in tiles_x:
                if tile['mine']:
                    tile['widget'].config(image=self.img_mine)
                    tile['discovered'] = True

    def execute_function_for_neighbors(self, x, y, func):
        for neighbor_x in range(x-1, x+2):
            if neighbor_x in range(0, self.width):
                for neighbor_y in range(y-1, y+2):
                    if (
                        neighbor_y in range(0, self.height) and not
                        (neighbor_x == x and neighbor_y == y)
                    ):
                        # prevent execution when the game stops in the meantime
                        if self.running:
                            func(neighbor_x, neighbor_y)

    def discover_neighbors_safe(self, x, y):
        """
        Discover neighbor fields when probably safe
        This means, that the amount of locked fields needs to equal the number
        on the current field.
        """
        if self.field[x][y]['number'] == 0:
            # 0-fields are safe by default,
            # since there are not any mines near them
            self.execute_function_for_neighbors(x, y, self.discover)
        else:
            lock_count = 0
            for neighbor_x in range(x-1, x+2):
                if neighbor_x in range(0, self.width):
                    for neighbor_y in range(y-1, y+2):
                        if (
                            neighbor_y in range(0, self.height) and not
                            (neighbor_x == x and neighbor_y == y) and
                            self.field[neighbor_x][neighbor_y]['locked']
                        ):
                            lock_count += 1
                            if lock_count >= self.field[x][y]['number']:
                                self.execute_function_for_neighbors(
                                    x, y, self.discover
                                )

    def discover(self, x, y):
        field = self.field[x][y]
        if not self.running and self.timer is not None:
            self.timer.start()
            self.running = True
        # check if field is locked or already discovered
        if not (field['locked'] or field['discovered']):
            field['discovered'] = True
            if field['mine']:
                # ouch! This was a mine +.+
                field['widget'].config(image=self.img_mine)
                self.game_over(False)
            else:
                # update image
                field['widget'].config(image=self.img_discovered)
                if field['number'] == 0:
                    # discover neighbor fields as well,
                    # since they are definitaly save
                    self.discover_neighbors_safe(x, y)
                else:
                    # display number
                    str_num = str(field['number'])
                    field['widget'].config(
                        text=str_num,
                        compound='center',
                        font='Arial 11 bold',
                        fg=self.numbercolors[str_num]
                    )
                    # add double-click function
                    # to discover all neighbors
                    field['widget'].bind(
                        '<Double-1>',
                        lambda e, x=x, y=y: self.discover_neighbors_safe(x, y)
                    )
                self.covered_fields -= 1
                if self.covered_fields == self.mine_count:
                    self.game_over(True)

    def toggle_lock(self, x, y):
        field = self.field[x][y]
        if not field['discovered']:
            if not field['locked']:
                field['widget'].config(image=self.img_covered_flag)
                field['locked'] = True
                self.update_minecounter(-1)
            else:
                field['widget'].config(image=self.img_covered)
                field['locked'] = False
                self.update_minecounter(1)
        return 'break'

    def set_difficulty(self, difficulty='easy', write=True):
        values = self.get_difficulty_values(difficulty)

        if values:
            self.difficulty = difficulty
            self.width = int(values['width'])
            self.height = int(values['height'])
            self.mine_count = int(values['mines'])
            try:
                self.ini.set('settings', 'difficulty', difficulty)
                self.ini.write(open('config.ini', 'w'))
                self.reset()
                return True
            except Exception:
                return False
        else:
            return False

    def get_difficulty(self):
        return self.difficulty

    def get_difficulty_values(self, difficulty):
        try:
            width, height, mines = self.ini.get(
                'difficulty', difficulty
            ).split(':')
            return {
                'width': width,
                'height': height,
                'mines': mines
            }
        except Exception:
            return False

    def set_difficulty_values(self, difficulty, values):
        try:
            self.ini.set('difficulty', difficulty, ':'.join(values))
            self.ini.write(open('config.ini', 'w'))
            return True
        except Exception:
            return False

    def update_minecounter(self, inc=1, reset=False):
        if self.tk_mine_counter is not None:
            if reset:
                self.tk_mine_counter.set(self.mine_count)
            else:
                self.tk_mine_counter.set(self.tk_mine_counter.get() + inc)

    def set_minecounter(self, tkvar):
        self.tk_mine_counter = tkvar
        self.tk_mine_counter.set(self.mine_count)

    def set_timer(self, timer):
        self.timer = timer

    def attach_gameover_handler(self, handler):
        self.gameover_handler = handler

    def is_running(self):
        return self.running

    def show_highscore(self):
        pass


class Timer():

    def __init__(self, tkvar, tkwidget):
        self.tk_time = tkvar
        self.tk_widget = tkwidget
        self.running = False
        self.reset()

    def count(self):
        if self.running:
            self.tk_time.set(self.tk_time.get() + 1)
            self.tk_widget.after(1000, self.count)

    def start(self):
        self.running = True
        self.tk_widget.after(1000, self.count)

    def stop(self):
        self.running = False

    def reset(self):
        self.time = 0
        self.tk_time.set(0)

if __name__ == '__main__':

    root = tk.Tk()
    # disable tear-off function for menus
    root.option_add('*tearOff', False)

    highscore = hs.Highscore()
    last_highscore = None

    img_mine = tk.PhotoImage(
        file=os.path.join('images', 'mine.gif')
    )
    img_time = tk.PhotoImage(
        file=os.path.join('images', 'time.gif')
    )

    center_icon_smilies = {
        'default': '(o_o)',
        'dead': '(+_+)',
        'fear': '(O_O)',
        'joy': '\(^-^)/'
    }

    style = ttk.Style()
    style.configure(
        'Headline.TLabel',
        foreground='#111',
        padding=5,
        font='Arial 20 bold'
    )
    style.configure(
        'Bold.TLabel',
        foreground='#333',
        padding=4,
        font='Arial 12 bold'
    )
    style.configure(
        'Highlight.TLabel',
        foreground='#399',
        padding=2,
        font='Arial 10 bold italic'
    )
    style.configure(
        'Entry.TLabel',
        foreground='#333',
        padding=2,
        font='Arial 10 bold'
    )
    style.configure(
        'Display.TLabel',
        foreground='#c00',
        background='#111',
        relief=tk.SUNKEN,
        padding=3,
        font='Arial 10 bold'
    )
    style.configure(
        'Smilie.TButton',
        foreground='#990',
        padding=3,
        font='Arial 10 bold'
    )

    def bind_release_event():
        global release_event_id
        release_event_id = root.bind(
            '<ButtonRelease-1>',
            lambda e: tk_str_button.set(center_icon_smilies['default'])
        )

    def gameover_handler(game, win):
        global release_event_id
        global last_highscore
        root.unbind(
            '<ButtonRelease-1>',
            release_event_id
        )

        add_entry = False
        tk_str_name = tk.StringVar()
        if win:
            tk_str_button.set(center_icon_smilies['joy'])
            difficulty = tk_str_difficulty.get()
            time = tk_int_timer.get()

            # default win-message
            title = 'Congratulations!'
            msg = 'You won!\nPassed time: %d seconds' % (time)
            if difficulty != 'custom':
                rank = highscore.check_time_rank(difficulty, time)
                if rank <= 10:
                    title = 'Highscore!'
                    msg = '''You got rank %d in %d seconds!
                        \nPlease enter your name:''' % (rank, time)
                    add_entry = True
                    last_highscore = '%s:%d' % (difficulty, rank)
        else:
            tk_str_button.set(center_icon_smilies['dead'])
            title = 'Oh no!'
            msg = 'You dieded to death...'

        def ok_command(*args):
            if (add_entry):
                name = tk_str_name.get()
                if (name == '' or name is None):
                    if messagebox.askyesno(
                        'Anonymous?',
                        'Do you really want to be listed as "Anonymous"?'
                    ):
                        name = 'Anonymous'
                    else:
                        return
                # add time + name to db
                highscore.add_entry(difficulty, (time, name))
                window.destroy()
                # show highscore (mark last added entry)
                show_highscore(difficulty)
            else:
                window.destroy()

            game.reset()
            tk_str_button.set(center_icon_smilies['default'])
            bind_release_event()

        # create window
        window = create_mandatory_window(root, title, ok_command)

        content_frame = ttk.Frame(window)
        content_frame.pack(padx=5)

        if win:
            smilie = 'joy'
        else:
            smilie = 'dead'
        ttk.Label(
            content_frame, text=center_icon_smilies[smilie],
            anchor='center', style='Bold.TLabel'
        ).grid(
            column=0, row=0
        )
        ttk.Label(content_frame, text=msg).grid(
            column=0, row=1, pady=5
        )
        if (add_entry):
            entry = ttk.Entry(content_frame, textvariable=tk_str_name)
            entry.grid(column=0, row=2, sticky='nesw')
            entry.bind('<Return>', ok_command)
        ttk.Button(content_frame, text='Ok', command=ok_command).grid(
            column=0, row=3, pady=10
        )

    def create_mandatory_window(root, title, exit_handler=None):
        # create window
        window = tk.Toplevel(root)
        window.title(title)
        window.tk.call('wm', 'iconphoto', window._w, img_mine)
        window.resizable(False, False)

        # attach close-event
        window.protocol("WM_DELETE_WINDOW", exit_handler)

        # make window stay at the top
        window.transient(root)
        window.focus()
        window.grab_set()

        return window

    def change_difficulty(difficulty=None):
        if difficulty is None:
            difficulty = tk_str_difficulty.get()
        if game.get_difficulty() != difficulty:
            if not game.is_running() or messagebox.askyesno(
                title='Change difficulty',
                message='''Do you really want to change the difficulty now?
                \n\nThis will reset your game and
                \nyour current progress will be lost...'''
            ):
                if difficulty == 'custom':
                    show_custom_difficulty_window()
                else:
                    game.set_difficulty(difficulty)

    def show_custom_difficulty_window():
        def apply_values():
            values = []
            for option in options:
                value = tk_values[option].get()
                if value < 5:
                    value = 5
                elif value > 999:
                    value = 999
                values.append(str(value))
            if game.set_difficulty_values('custom', values):
                game.set_difficulty('custom')
            window.destroy()

        # create window and frame
        window = create_mandatory_window(
            root, 'Configurate Custom Difficulty', apply_values
        )
        window.bind('<Return>', lambda e: apply_values())
        content_frame = ttk.Frame(window)
        content_frame.pack(padx=5)

        # infotext
        ttk.Label(
            content_frame, text='Configurate custom-difficulty parameters'
        ).grid(column=0, columnspan=2, row=0, pady=5)

        # build input fields
        options = ['width', 'height', 'mines']
        values = game.get_difficulty_values('custom')
        tk_values = {}
        row = 1
        for option in options:
            ttk.Label(
                content_frame, text=option
            ).grid(column=0, row=row, padx=2, pady=2)
            tk_values[option] = tk.IntVar()
            tk_values[option].set(int(values[option]))
            tk.Spinbox(
                content_frame, textvariable=tk_values[option],
                from_=5, to=999, increment=1, wrap=True
            ).grid(column=1, row=row, padx=2, pady=2)
            row += 1

        # ok button
        ttk.Button(
            content_frame, text='Ok',
            command=apply_values
        ).grid(column=0, columnspan=2, row=row, pady=5)

    def reset_game(*args):
        if not game.is_running() or messagebox.askyesno(
            title='Restart current game',
            message='''Do you really want to restart?
            \n\nYour current progress will be lost...'''
        ):
            game.reset()

    def exit_game(*args):
        if not game.is_running() or messagebox.askyesno(
            title='Exit MinesweePy',
            message='''Do you really want to quit?
            \n\nYour current progress will be lost...'''
        ):
            root.destroy()

    def show_about_window(*args):
        messagebox.showinfo(
            title='About MinesweePy',
            message='''Version: %s
                \n
                \nCopyright 2016 by sol-develop.de''' % VERSION
        )

    def show_highscore(difficulty='current'):
        if difficulty == 'current':
            difficulty = tk_str_difficulty.get()
        if difficulty not in ('easy', 'medium', 'hard'):
            difficulty = 'easy'

        window = create_mandatory_window(root, 'Highscores')

        highscore_frame = ttk.Frame(window)
        highscore_frame.pack()
        ttk.Label(
            highscore_frame, text='Highscores', style='Headline.TLabel'
        ).pack()
        notebook = ttk.Notebook(highscore_frame)
        notebook.pack()

        tabs = {
            'easy': add_highscore_tab('easy', notebook),
            'medium': add_highscore_tab('medium', notebook),
            'hard': add_highscore_tab('hard', notebook)
        }

        # open the tab of the difficulty defined by the parameter
        notebook.select(tabs[difficulty])

        ttk.Button(
            highscore_frame, text='Close', command=window.destroy
        ).pack()

    def add_highscore_tab(
        difficulty, tk_notebook=None, refresh=False, tab=None
    ):
        global last_highscore

        highlight_rank = 0
        if last_highscore:
            lh = last_highscore.split(':')
            if difficulty == lh[0]:
                highlight_rank = int(lh[1])
                last_highscore = False

        if refresh and tab is not None:
            for widget in tab.winfo_children():
                widget.destroy()
        elif tk_notebook is not None:
            tab = ttk.Frame(tk_notebook)
            tk_notebook.add(tab, text=difficulty.title())
        else:
            return False
        ttk.Label(
            tab, text='Rank', width=10, style='Bold.TLabel'
        ).grid(column=0, row=0)
        ttk.Label(
            tab, text='Time', width=10, style='Bold.TLabel'
        ).grid(column=1, row=0)
        ttk.Label(
            tab, text='Player', width=30, style='Bold.TLabel'
        ).grid(column=2, row=0)
        row = 1
        for entry in highscore.get_all_entries(difficulty):
            if highlight_rank == row:
                style = 'Highlight.TLabel'
            else:
                style = 'Entry.TLabel'
            ttk.Label(
                tab, text=row, width=10, anchor='w', style=style
            ).grid(column=0, row=row)
            ttk.Label(
                tab, text=entry[0], width=10, anchor='w', style=style
            ).grid(column=1, row=row)
            ttk.Label(
                tab, text=entry[1], width=30, anchor='w', style=style
            ).grid(column=2, row=row)
            row += 1
        ttk.Button(
            tab, text='Delete Highscore',
            command=lambda: delete_highscore(difficulty, tab)
        ).grid(column=2, row=row, pady=5, sticky=tk.E)
        return tab

    def delete_highscore(difficulty, tab):
        if messagebox.askyesno(
            'Delete Highscore',
            'Do you really want to delete the Highscore for %s difficulty?'
            % difficulty
        ):
            highscore.delete_all_entries(difficulty)
            # refresh tab
            add_highscore_tab(difficulty, None, True, tab)

    # set window title and icon
    root.title('MinesweePy')
    root.tk.call('wm', 'iconphoto', root._w, img_mine)
    root.resizable(False, False)

    # capture window-close event
    root.protocol("WM_DELETE_WINDOW", exit_game)

    # menu
    menubar = tk.Menu(root)
    root['menu'] = menubar

    menu_game = tk.Menu(menubar)
    menubar.add_cascade(menu=menu_game, label='Game')
    menu_game.add_command(label='Restart', command=reset_game)
    menu_game.add_separator()
    menu_game.add_command(label='Show Highscores', command=show_highscore)
    menu_game.add_separator()
    menu_game.add_command(label='Quit', command=exit_game)

    tk_str_difficulty = tk.StringVar()
    menu_diffulty = tk.Menu(menubar)
    menubar.add_cascade(menu=menu_diffulty, label='Difficulty')
    menu_diffulty.add_radiobutton(
        label='Easy', variable=tk_str_difficulty, value='easy',
        command=change_difficulty
    )
    menu_diffulty.add_radiobutton(
        label='Medium', variable=tk_str_difficulty, value='medium',
        command=change_difficulty
    )
    menu_diffulty.add_radiobutton(
        label='Hard', variable=tk_str_difficulty, value='hard',
        command=change_difficulty
    )
    menu_diffulty.add_separator()
    menu_diffulty.add_radiobutton(
        label='Custom', variable=tk_str_difficulty, value='custom',
        command=change_difficulty
    )

    menu_help = tk.Menu(menubar)
    menubar.add_cascade(menu=menu_help, label='Help')
    menu_help.add_command(label='About..', command=show_about_window)

    # mainframe
    mainframe = ttk.Frame(root)
    mainframe.pack()
    # mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

    # top bar for minecount, timer and reset-button
    tk_int_mines = tk.IntVar()
    tk_int_timer = tk.IntVar()
    tk_str_button = tk.StringVar()
    tk_str_button.set(center_icon_smilies['default'])
    top_bar = ttk.Frame(mainframe)
    top_bar.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    lbl_img_mines = ttk.Label(
        top_bar, image=img_mine
    )
    lbl_img_mines.grid(column=0, row=0, sticky=tk.W)
    lbl_mines = ttk.Label(
        top_bar, textvariable=tk_int_mines, anchor=tk.W,
        style='Display.TLabel', width=5
    )
    lbl_mines.grid(column=1, row=0, sticky=tk.W)
    btn_state = ttk.Button(
        top_bar, textvariable=tk_str_button, style='Smilie.TButton'
    )
    btn_state.grid(column=3, row=0)
    lbl_timer = ttk.Label(
        top_bar, textvariable=tk_int_timer, anchor=tk.E,
        style='Display.TLabel', width=5
    )
    lbl_timer.grid(column=5, row=0, sticky=tk.E)
    lbl_img_mines = ttk.Label(
        top_bar, image=img_time
    )
    lbl_img_mines.grid(column=6, row=0, sticky=tk.W)

    top_bar.columnconfigure(2, weight=1)
    top_bar.columnconfigure(4, weight=1)

    # field frame
    field_frame = ttk.Frame(mainframe)
    field_frame.grid(column=0, row=1)

    # statusbar
    status_bar = ttk.Frame(mainframe)
    status_bar.grid(column=0, row=2, sticky=(tk.N, tk.W, tk.E, tk.S))
    lbl_difficulty = ttk.Label(
        status_bar, textvariable=tk_str_difficulty, anchor=tk.W
    )
    lbl_difficulty.grid(column=0, row=0, sticky=tk.W)

    # create timer
    timer = Timer(tk_int_timer, lbl_timer)

    # attach widgets to the game
    game = MinesweePy(field_frame)
    game.set_minecounter(tk_int_mines)
    game.set_timer(timer)
    game.attach_gameover_handler(gameover_handler)
    btn_state.config(command=reset_game)
    tk_str_difficulty.set(game.get_difficulty())

    # create feared smilie event
    root.bind(
        '<Button-1>',
        lambda e: tk_str_button.set(center_icon_smilies['fear'])
    )
    bind_release_event()

    root.mainloop()
