import math
import tkinter.filedialog as tk


class Sample:
    # Класс объектов, содержащих достаточные данные (номер строки, номер пробы, концентрация) о пробах в файле.
    def __init__(self, number_of_raw, number, conc):
        self.number = number
        self.conc = conc
        self.number_of_raw = number_of_raw

    def __repr__(self):
        return str(self.number_of_raw) + '\t' + self.number + '\t' + self.conc + '\n'


class SampleList(list):
    # Создание списка из объектов, содержащих данные о пробах и их упорядочение.
    def __init__(self, file: str):
        super().__init__()
        file_text = SampleList.load_file(file)
        # Откртытие файла с прибора.
        for element in SampleList.parse_file_text(file_text):
            self.append(element)
            # Заполнение списка строчками из файла.

    def resume_processing(self, first_raw, last_raw):
        # Выполнение метода происходит только после нажатия кнопки продолжения работы, после указания необходимых
        # строчек.
        meaningful_samples = self.select_meaningful_lines(first_raw, last_raw)
        self.clear()
        for element in SampleList.order_samples(meaningful_samples):
            self.append(element)
            # Заполнение списка только с теми строчками, в которых находятся даные о пробах.

    @staticmethod
    def parse_file_text(file_text):
        # Разделение строчки на отдельные части и назначение полей класса Sample.
        i = 0
        for line in file_text:
            parts = str.split(line, '\t')
            # Извлечение названия и значения пробы из каждой строки в кортеж.
            if parts[0] == 'True':
                yield Sample(i, parts[3], parts[5] if parts[5] != '' else '0') 
                i += 1

    @staticmethod
    def load_file(name_of_file):
        # Открытие файла и создание списка из строк.
        file = open(name_of_file)
        lines = file.readlines()
        file.close()
        return lines

    def select_meaningful_lines(self, first_raw, last_raw):
        # Извлечение строк, которые необходимо обработать.
        start_index = first_raw
        # Задание номеров строк из интерфейса.
        end_index = last_raw+1
        list_for_self = self[start_index:end_index]
        return list_for_self

    @staticmethod
    def remove_nondigits(name):
        # Удаление из навзваний проб символов, отличных от порядковых номеров.
        result = tk.re.sub('[^0-9]', '', name)
        if len(result) > 0:
            return int(result)
        return -1

    @staticmethod
    def order_samples(list_of_samples):
        # Сортировка листа объектов по названиям проб.
        return sorted(list_of_samples, key=lambda sample: (SampleList.remove_nondigits(sample.number)))


class StatisticsSamples:
    # создание списка упорядоченных объектов
    def __init__(self, number, conc1, conc2, aver, perc, com):
        self.number = number
        self.conc1 = conc1
        self.conc2 = conc2
        self.aver = aver
        self.perc = perc
        self.com = com

    def __repr__(self):
        return self.number + '\t' + str(self.conc1) + '\t' + str(self.conc2) + '\t' + str(self.aver) + '\t'\
               + str(self.perc) + '\t' + self.com + '\n'


class ListOfStatisticsSamples(list):
    # Подготовка списка к статистической обработке.
    def __init__(self, source_samples: SampleList, quantity: int):
        # Спаривание строчек со значениями концентраций для одной пробы.
        super().__init__()
        for i in range(0, len(source_samples)-1, 2):
            element = source_samples[i]
            element2 = source_samples[i+1]
            self.append(StatisticsSamples(element.number, float(element.conc), float(element2.conc), 0, 0, []))

            ListOfStatisticsSamples.calculate_average(self, quantity)
            ListOfStatisticsSamples.calculate_percent(self)
            ListOfStatisticsSamples.generate_comments(self)
            # Заполнение остальных полей класса, величина quantity задаётся из интерфейса и является величиной проб,
            # взятых в анализ в мкл.

    @staticmethod
    def calculate_average(collected_samples, quantity: int):
        # Для вычисления среднего необходимо задать количество микролитров пробы.
        quan = quantity
        for element in collected_samples:
            element.aver = round(((element.conc1 + element.conc2)/2)/quan, 2)

    @staticmethod
    def calculate_percent(collected_samples):
        # Рассчет процента отличия первой концентрации пробы от второй (сравнение двух повторов).
        for element in collected_samples:
            if element.conc1 != 0 and element.conc2 != 0:
                # Если одна из концетраций равна нулю, то такая проба отмечается в методе "создать коммертарий" как
                # плохая.
                bigger = max([element.conc1, element.conc2])
                element.perc = round(((math.fabs(element.conc1-element.conc2))/bigger*100), 1)

    @staticmethod
    def generate_comments(collected_samples):
        for element in collected_samples:
            comments = []

            def calculate_precision():
                # Если процент различия концентраций проб больше 30, то проба плохая.
                precision = ''
                if element.perc > 30:
                    precision = 'bad'
                return precision

            def calculate_accuracy():
                # Если концентрация меньше определнной величины, то в пробе нет гена и есть только грязь.
                accuracy = ''
                if element.conc1 < 0.01 or element.conc2 < 0.01:
                    accuracy = 'bad'
                return accuracy

            def calculate_zero_result():
                # Если одна из концентраций ноль, то этт выпадающее значение.
                zero_result = ''
                if element.conc1 == 0 or element.conc2 == 0:
                    zero_result = 'exist'
                return zero_result

            comments.append(calculate_precision())
            comments.append(calculate_accuracy())
            comments.append(calculate_zero_result())
            element.com = '\t'.join(comments)
            # Комментарии заполняют список, который потом становится значением поля класса StatisticSamoles.


class LogicLayer:
    # Создание логической части интерфейса,

    def open_work_file(self):
        # Метод кнопки открытия файла, возвращает набор строчек и полное имя файла.
        open_path = tk.askopenfilename()
        file_name = open_path
        self.samples = SampleList(file_name)
        result = ''
        for sample in self.samples:
            result += sample.__repr__()
        return result, file_name

    def resume_processing(self, first_raw, last_raw, quantity):
        # Метод продолжения работы после указания рабочих строк, количества проб, возвращает обработанные упорядоченные
        # пробы.
        self.samples.resume_processing(first_raw, last_raw)
        self.tempsamples = ListOfStatisticsSamples(self.samples, quantity)
        result = ''
        for sample in self.tempsamples:
            result += sample.__repr__()
        return result

    def save_results_to_file(self):
        # Метод сохранения результата в текстовый файл построчно.
        save_path = tk.asksaveasfilename(filetypes=[('text files', '.txt'), ('all files', '.*')],
                                         initialfile='ordered_results.txt')
        file = open(save_path, 'w')
        file.write('number' + '\t' + 'conc1' + '\t' + 'conc2' + '\t' + 'aver' + '\t' + 'perc' + '\t' + 'precision' +
                   '\t' + 'accuracy' + '\t' + 'zero' + '\n')
        print('number' + '\t' + 'conc1' + '\t' + 'conc2' + '\t' + 'aver' + '\t' + 'perc' + '\t' + 'precision' + '\t' +
              'accuracy' + '\t' + 'zero')
        for sample in self.tempsamples:
            file.write(str(sample))
            print(sample)
        file.close()


class Interfacing:
    # Класс для графического отображения интерфейса.

    def __init__(self):
        self.logic = LogicLayer()
        root = tk.Tk()
        root.title('Processing raw data')
        # Создание основного окна.
        root.minsize(600, 400)
        # self.len, self.wieg = root.minsize()

        right_frame = tk.Frame(root)
        # Рамка в основном окне справа для упорядочения положения кнопок.
        self.open_button = tk.Button(right_frame, text='Open file', command=self.open_work_file)
        self.open_button.pack(side='top', fill='x')
        texts_frame = self.create_text_elements_frame(right_frame)
        texts_frame.pack(side="top", pady=10)
        # Рамка в правой рамке окна для полей с номерами строк и размера проб.
        self.resume_button = tk.Button(right_frame, text='Resume', command=self.resume_processing)
        self.resume_button.pack(side='top', fill='x')

        self.save_button = tk.Button(right_frame, text='Save', command=self.logic.save_results_to_file)
        self.save_button.pack(side='bottom', fill='x')
        right_frame.pack(side='right', fill='y', pady=4, padx=2)

        self.left_frame = tk.Frame(root)
        # Рамка слева в основном окне для поля адреса, кнопки открытия файла, текстового поля со строчками файла и
        # скроллбара.
        self.filename_entry = tk.Entry(self.left_frame)
        self.filename_entry.insert(0, 'Select file...')
        self.filename_entry.pack(side="top", fill="x", expand=False)

        self.header_text = tk.Label(self.left_frame, text='', anchor='w')
        self.header_text.pack(side="top", fill="x")
        # Заголовки столбцов над текстовым полем для лучшего восприятия текста в текстовом поле.

        self.list_of_sam_in_ob_box = tk.Text(self.left_frame)
        self.list_of_sam_in_ob_box.pack(side='top', fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.list_of_sam_in_ob_box)
        self.scrollbar.pack(side='right', fill='y')
        self.scrollbar['command'] = self.list_of_sam_in_ob_box.yview
        self.list_of_sam_in_ob_box['yscrollcommand'] = self.scrollbar.set
        self.left_frame.pack(fill='both', side="left", expand=True, pady=4, padx=2)

        root.mainloop()

    def open_work_file(self):
        # Результат работы кнопки "открыть файл".
        text, file_path_text = self.logic.open_work_file()
        self.filename_entry.delete(0, tk.END)
        self.filename_entry.insert(0, file_path_text)
        # Строки из файла печатаются в текстовом поле.
        if text == '':
            error_text = 'Wrong file'
            self.open_error_window(error_text)
        self.list_of_sam_in_ob_box.insert(tk.END, text)

    def resume_processing(self):
        # Результат работы кнопки "Resume".
        # В текстовом поле выводится результат обработки проб.
        if self.first_raw_tb.get() != '' and self.last_raw_tb.get() != '' and self.quantity_tb.get() != '' and \
                        int(self.quantity_tb.get()) > 0 and int(self.first_raw_tb.get())>= 0 and \
                        int(self.first_raw_tb.get()) < 97 and int(self.last_raw_tb.get()) < 97 and \
                        int(self.last_raw_tb.get()) > int(self.first_raw_tb.get()):
            text = self.logic.resume_processing(int(self.first_raw_tb.get()), int(self.last_raw_tb.get()),
                                                int(self.quantity_tb.get()))
            self.list_of_sam_in_ob_box.delete(1.0, tk.END)
            self.list_of_sam_in_ob_box.insert(tk.END, text)
            self.list_of_sam_in_ob_box.config(state=tk.DISABLED)
        else:
            error_text = 'Wrong row range'
            self.open_error_window(error_text)
        self.header_text['text'] = 'number      conc1         conc2         aver         perc         precision      ' \
                                   'accuracy      zero'

    def create_text_elements_frame(self, right_frame):
        # Создание рамки в правой рамке окна для полей с номерами строк и размера проб.
        texts_frame = tk.Frame(right_frame)
        tk.Label(texts_frame, text="First raw").grid(column=0, row=0, padx=2, pady=2)
        tk.Label(texts_frame, text="Last raw").grid(column=0, row=1, padx=2, pady=2)
        tk.Label(texts_frame, text="Quantity").grid(column=0, row=2, padx=2, pady=2)

        self.first_raw_tb = tk.Entry(texts_frame, width=4)
        self.last_raw_tb = tk.Entry(texts_frame, width=4)
        self.quantity_tb = tk.Entry(texts_frame, width=4)

        self.first_raw_tb.grid(column=1, row=0)
        self.last_raw_tb.grid(column=1, row=1)
        self.quantity_tb.grid(column=1, row=2)
        return texts_frame

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
