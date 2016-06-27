

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

    print('Can not execute timer directly')
