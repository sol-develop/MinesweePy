import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
from src import highscore as hs
from src import minesweepy
from src import timer

VERSION = '1.0.0 beta'


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
    timer = timer.Timer(tk_int_timer, lbl_timer)

    # attach widgets to the game
    game = minesweepy.MinesweePy(field_frame)
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
