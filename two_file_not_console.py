from enum import Enum
import tkinter.filedialog as tk


class Sample: 
    # Класс для объектов из списков. один объект - одна проба.
    def __init__(self, number, conc, control, line):
        self.number = number
        self.conc = conc
        self.control = control
        self.line = line

    def __repr__(self):
        return str(self.number) + '\t' + str(self.conc) + '\t' + str(self.control) + '\t' + str(self.line) + '\n'


class ParsingType(Enum): 
    # Типы разделения в зависимости от типа входного файла - с концентрациями или названиями групп.
    sample_average = 0
    group_name = 1


class GeneSampleList(list): 
    # Лист для проб с целевым геном.
    def __init__(self, file_name: str, parsing_type: ParsingType):
        super().__init__()
        file_text = GeneSampleList.load_file(file_name)
        for element in GeneSampleList.parse_file_text(file_text, parsing_type):
            # Элементы добавляются в лист построчно из файла.
            self.append(element)

    @staticmethod
    def parse_file_text(file_text, parsing_type): 
        # Разделение строчки на отдельные части и назначение полей класса Sample. В зависимости от типа может делить как
        #  обычный файл с пробами или как файл с названиями групп.
        if parsing_type == ParsingType.sample_average:
            for line in file_text[1:]:
                parts = str.split(line)
                parts[0] = tk.re.sub('\D', '', parts[0])
                yield Sample(parts[0], parts[3] if parts[3] != '' else '0', '', '')
        elif parsing_type == ParsingType.group_name:
            for line in file_text[1:]:
                parts = str.split(line, ';')
                # parts[0] = tk.re.sub('\D', '', parts[0])
                try:
                    yield Sample(parts[0], '', parts[1], parts[2])
                except IndexError:
                    yield Sample(parts[0], '', parts[1].strip('\n'), '\n')

    @staticmethod
    def load_file(file_name):
        # Открытие файла и создание списка из строк.
        file = open(file_name)
        lines = file.readlines()
        file.close()
        return lines


class ComparativeSampleList(GeneSampleList): 
    # Лист для проб референсного гена.
    def __init__(self, file_name: str, parsing_type):
        super().__init__(file_name, parsing_type)


class GroupNameList(GeneSampleList): 
    # Лист для названий групп для каждой пробы.
    def __init__(self, file_name: str, parsing_type):
        super().__init__(file_name, parsing_type)


class SampleReadyForProcessing: 
    # Класс объектов, где каждый объект - одна проба со своим номером, отношением целевого гена к референсному в ста
    # копиях, названия линий (контроль/эксперимент, типы эксперимента).
    def __init__(self, number, comparison, control, line):
        self.number = number
        self.comparison = comparison
        self.control = control
        self.line = line

    def __repr__(self):
        return self.number + '\t' + str(self.comparison) + '\t' + self.control.replace(' ', '_') + '\t' + self.line


class ListSampleForProcessing(list): 
    # Класс-список с объектами-пробами.
    def __init__(self, gene_list: GeneSampleList, comparative_list: ComparativeSampleList, group_list: GroupNameList):
        super().__init__()
        # Comparing gene item, comparative item and group item by fist field in class - number of item.
        for i in range(0, len(gene_list)):
            number_of_item = gene_list[i].number
            for comparative_item in comparative_list:
                if comparative_item.number == number_of_item:
                    comparison = 0.0
                    if comparative_item != 0:
                        comparison = round(((float(gene_list[i].conc)/float(comparative_item.conc))*100), 3)
                        # Сравнение целевого гена с референсным в ста копиях.
                    for group_item in group_list:
                        if group_item.number == number_of_item:
                            self.append(SampleReadyForProcessing(gene_list[i].number, comparison, group_item.control,
                                                         group_item.line))

class LogicLayer: 
    # Логическая составляющая интерфейса.

    def open_gene_file(self):
        # Метод кнопки открытия файла с целевым геном, возвращает набор строчек и полное имя файла.
        open_path = tk.askopenfilename()
        self.gene_file_name = open_path
        return open_path

    def open_comparative_file(self):
        # Метод кнопки открытия файла с референсным геном, возвращает набор строчек и полное имя файла.
        open_path = tk.askopenfilename()
        self.comparative_file_name = open_path
        return open_path

    def open_group_file(self):
        # Метод кнопки открытия файла с названиями групп, возвращает набор строчек и полное имя файла.
        open_path = tk.askopenfilename()
        self.group_file_name = open_path
        return open_path

    def resume_processing(self):
        # Метод продолжения работы после указания всех фалов, возвращает обработанные упорядоченные пробы.
        gene = GeneSampleList(self.gene_file_name, ParsingType.sample_average)
        comparative = ComparativeSampleList(self.comparative_file_name, ParsingType.sample_average)
        group = GroupNameList(self.group_file_name, ParsingType.group_name)
        self.tempsamples = ListSampleForProcessing(gene, comparative, group)
        result = ''
        for sample in self.tempsamples:
            result += sample.__repr__()
        return result

    def save_results_to_file(self):
        # Метод сохранения результата в текстовый файл построчно.
        save_path = tk.asksaveasfilename(filetypes=[('text files', '.txt'), ('all files', '.*')],
                                         initialfile='proANOVA.txt')
        file = open(save_path, 'w')
        file.write('number\tmean\tline\n')
        print('number\tmean\tline')
        for sample in self.tempsamples:
            file.write(str(sample))
            print(sample)
        file.close()


class Interfacing:
    # Класс для графического отображения интерфейса.

    def __init__(self):
        self.logic = LogicLayer()
        root = tk.Tk()
        root.title('Create full list')
        # Создание основного окна.
        root.minsize(600, 400)
        # self.len, self.wieg = root.minsize()

        right_frame = tk.Frame(root) 
        # Рамка справа в основном окне для упорядочения кнопок открытия.
        self.gene_button = tk.Button(right_frame, text='Open gene file', command=self.open_gene_file)
        self.gene_button.pack(side='top', fill='x')

        self.comparative_button = tk.Button(right_frame, text='Open reference file', command=self.open_comparative_file)
        self.comparative_button.pack(side='top', fill='x')

        self.group_button = tk.Button(right_frame, text='Open group file', command=self.open_group_file)
        self.group_button.pack(side='top', fill='x')

        self.resume_button = tk.Button(right_frame, text='Resume', command=self.resume_processing)
        self.resume_button.pack(side='top', fill='x', pady=15,)

        self.save_button = tk.Button(right_frame, text='Save', command=self.logic.save_results_to_file)
        self.save_button.pack(side='bottom', fill='x')
        right_frame.pack(side='right', fill='y', pady=4, padx=2)

        left_frame = tk.Frame(root)
        # Рамка слева в основном окне для упорядочения полей для путей.
        self.gene_entry = tk.Entry(left_frame)
        self.gene_entry.insert(0, 'Select gene file...')
        self.gene_entry.pack(side="top", fill="x", expand=False)

        self.comparative_entry = tk.Entry(left_frame)
        self.comparative_entry.insert(0, 'Select reference gene file...')
        self.comparative_entry.pack(side="top", fill="x", pady=5, expand=False)

        self.group_entry = tk.Entry(left_frame)
        self.group_entry.insert(0, 'Select group file...')
        self.group_entry.pack(side="top", fill="x", pady=5, expand=False)

        self.header_text = tk.Label(left_frame, text='', anchor='w')
        self.header_text.pack(side="top", fill="x")
        # Заголовки столбцов над текстовым полем для лучшего восприятия текста в текстовом поле.

        self.list_of_sam_in_ob_box = tk.Text(left_frame) 
        # Текстовое поле со скроллбаром, в котором отображается результат обработки значений проб.
        self.list_of_sam_in_ob_box.pack(side='top', fill="both", expand=True)
        self.scrollbar = tk.Scrollbar(self.list_of_sam_in_ob_box)
        self.scrollbar.pack(side='right', fill='y')
        self.scrollbar['command'] = self.list_of_sam_in_ob_box.yview
        self.list_of_sam_in_ob_box['yscrollcommand'] = self.scrollbar.set
        left_frame.pack(fill='both', side="left", expand=True, pady=4, padx=2)

        root.mainloop()

    def open_gene_file(self): 
        # Записывает путь до файла с целевым геном в поле пути.
        file_path_text = self.logic.open_gene_file()
        self.gene_entry.delete(0, tk.END)
        self.gene_entry.insert(0, file_path_text)

    def open_comparative_file(self):
        # Записывает путь до файла с референсным геном в поле пути.
        file_path_text = self.logic.open_comparative_file()
        self.comparative_entry.delete(0, tk.END)
        self.comparative_entry.insert(0, file_path_text)

    def open_group_file(self):
        # Записывает путь до файла с названиями групп в поле пути.
        file_path_text = self.logic.open_group_file()
        self.group_entry.delete(0, tk.END)
        self.group_entry.insert(0, file_path_text)

    def resume_processing(self): 
        # Продолжает работу, заполняя текстовое поле результатом обработки значений проб.
        # try:
            text = self.logic.resume_processing()
            self.list_of_sam_in_ob_box.delete(1.0, tk.END)
            self.list_of_sam_in_ob_box.insert(1.0, text)
            self.list_of_sam_in_ob_box.config(state=tk.DISABLED)
            self.header_text['text'] = 'number      mean         line'
        # except Exception:
        #     error_text = 'Wrong file(s)'
        #     self.open_error_window(error_text)

    def open_error_window(self, error_text):
        error = tk.Tk()
        error.title('Error')
        # Создание окна с ошибкой.
        error.minsize(100, 50)
        # error.wm_geometry("+self.len/2+self.wieg/2")

        # frame = tk.Frame(error)
        self.error = tk.Label(error, text=error_text)
        self.error.pack(fill='x')

        self.ok_button = tk.Button(error, text='Ok', command=error.destroy)
        self.ok_button.pack(side='bottom')

        # frame.pack(fill='both')
        error.mainloop()

def start():
    faceing = Interfacing()
    # Запуск программы.
