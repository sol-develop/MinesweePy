import tkinter as tk
from configparser import ConfigParser
import random
import os

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
        self.timer.stop()
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
