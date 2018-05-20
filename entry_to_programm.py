import tkinter.filedialog as tk
import one_file_not_console
import two_file_not_console
import new_statistics_methods
import os


class Interfacing:
    def __init__(self):
        # Отображение начального диалогового окна, которое предоставляет выбор ко всем функциям программы
        root = tk.Tk()
        root.title('PCR processing')
        # Создание основного окна.
        root.minsize(600, 400)

        self.one_file_not_console_button = tk.Button(root, text='Processing raw data', command=one_file_not_console.start)
        self.one_file_not_console_button.pack(side='top', fill='x', padx=20, pady=5)

        self.two_file_not_console_button = tk.Button(root, text='Create full list', command=two_file_not_console.start)
        self.two_file_not_console_button.pack(side='top', fill='x',  padx=20, pady=5)

        self.new_statistics_methods_button = tk.Button(root, text='Statistic processing', command=new_statistics_methods.start)
        self.new_statistics_methods_button.pack(side='top', fill='x',  padx=20, pady=5)

        self.help_button = tk.Button(root, text='Help', command=self.help)
        self.help_button.pack(side='top', fill='x',  padx=20, pady=5)

        self.whats_new_button = tk.Button(root, text="What's new", command=self.whats_new)
        self.whats_new_button.pack(side='top', fill='x', padx=20, pady=5)

        self.about_button = tk.Button(root, text='About program', command=self.about_window)
        self.about_button.pack(side='top', padx=20, pady=5)

        root.mainloop()

    @staticmethod
    def help():
        os.system('readme.txt')

    def whats_new(self):
        whats_new = tk.Tk()
        whats_new.title("What's new")
        whats_new.minsize(300, 150)

        self.whats_new = tk.Label(whats_new, text='What is new in v0.3\n'
                                                  '> Fixed bug with one-way ANOVA, when degree of freedom was not '
                                                  'clear\n'
                                                  '> Fixed comparing lists by name of items, not by thier position in '
                                                  'the lists\n'
                                                  "> Create What's new button")
        self.whats_new.pack(fill='x')

        whats_new.mainloop()

    def about_window(self):
        about = tk.Tk()
        about.title('About')
        about.minsize(300, 150)

        self.about = tk.Label(about, text='PCR processing\nProgram for processing PCR RT data from\nRoche LightCycler® '
                                          '480 System\n\n\n'
                                          'Version: May, 2018, 0.3\n\n\nAuthors: Arina Pershina, Michael Timoshin\n'
                                          'june38@yandex.ru')
        self.about.pack(fill='x')

        about.mainloop()

faceing = Interfacing()