import functools
import scipy
from scipy import stats
import numpy
from enum import Enum
import tkinter.filedialog as tk


class PreparedSample:
    # Класс объектов-проб, получаемых из файла.
    def __init__(self, number, conc, control, line, comment):
        self.number = number
        self.conc = conc
        self.control = control
        self.line = line
        self.comment = comment
        self.is_checked = True

    def __repr__(self):
        return self.number + '\t' + str(self.conc) + '\t' + self.control + '\t' + self.line + '\t' + str(self.comment)


class SampleList(list):
    # Список объектов проб.
    def __init__(self, file_name: str):
        super().__init__()
        file_text = SampleList.load_file(file_name)
        for element in SampleList.parse_file_text(file_text):
            self.append(element)

    @staticmethod
    def parse_file_text(file_text):
        # Разделение строчки на отдельные части и назначение полей класса Sample.
        for line in file_text[1:]:
            parts = str.split(line)
            try:
                yield PreparedSample(parts[0], float(parts[1]), parts[2], parts[3], '')
            except IndexError:
                yield PreparedSample(parts[0], float(parts[1]), parts[2], 0, '')

    @staticmethod
    def load_file(file_name):
        # Открытие файла и создание списка из строк.
        file = open(file_name)
        lines = file.readlines()
        file.close()
        return lines


class SampleListWithoutBads(list):
    # Лист объектов-проб, из которого исключены плохие пробы при помощи чек-боксов в интерфейсе.
    def __init__(self, source_samples: list):
        super().__init__()
        processed_list = [element for element in source_samples if element.is_checked == True]
        for element in processed_list:
            self.append(element)


class GroupType(Enum):
    # Способы группирования объектов.
    Normal = 0
    Control = 1
    Line = 2


class GroupedSamples(list):
    # Лист, который внутри имеет группы, состоящие из объектов. Группы сформированы в зависимости от типа группировки.
    def __init__(self, source_samples: list, group_type: GroupType):
        super().__init__()
        sorted_samples = GroupedSamples.sort_samples(source_samples, group_type)
        if group_type == GroupType.Control:
            # Группировка по контролю/эксперименту.
            for sample_group in GroupedSamples.group_samples_by_control(sorted_samples):
                self.append(sample_group)
        else:
            for sample_group in GroupedSamples.group_samples(sorted_samples):
                # Группировка по типу эксперементального воздействия.
                self.append(sample_group)

    def to_conc_lists(self):
        # Превращение листа с группами объектов в лист с группами чисел-концентраций.
        result = []
        for group in self:
            inner_group = [x.conc for x in group]
            result.append(numpy.asarray(inner_group))
        return result

    @staticmethod
    def sort_samples(source_samples, group_type: GroupType):
        # Сортировка объектов в зависимости от типа группировки. В конце всех сортировок внутри каждой группы объекты
        # сортированы по увеличению концентраций.
        result = []
        if group_type == GroupType.Normal:
            result = sorted(source_samples, key=lambda item: (item.control, item.line, item.conc))
        elif group_type == GroupType.Control:
            result = sorted(source_samples, key=lambda item: (item.control, item.conc))
        elif group_type == GroupType.Line:
            result = sorted(source_samples, key=lambda item: (item.line, item.conc))
        return result

    @staticmethod
    def group_samples(sorted_samples):
        # Создание групп из объектов, основываясь на поле линия (влияния линия не заполнено, то объект пропускается.
        if len(sorted_samples) > 0:
            templist = []
            temp_group = []
            temp_line = None
            for elem in sorted_samples:
                if elem.line == '0':
                    continue
                if elem.line == temp_line:
                    temp_group.append(elem)
                else:
                    if len(temp_group) > 0:
                        yield temp_group
                    temp_group = [elem]
                    temp_line = elem.line
            yield temp_group
            templist.append(temp_group)

    @staticmethod
    def group_samples_by_control(sorted_samples):
        # Создание групп из объектов, основываясь на поле контроль (конторль/эксперимент).
        if len(sorted_samples) > 0:
            templist = []
            temp_group = []
            temp_control = None
            for elem in sorted_samples:
                if elem.control == '0':
                    continue
                if elem.control == temp_control:
                    temp_group.append(elem)
                else:
                    if len(temp_group) > 0:
                        yield temp_group
                    temp_group = [elem]
                    temp_control = elem.control
            yield temp_group
            templist.append(temp_group)


class GroupStatistics(GroupedSamples):
    def __init__(self, source_samples: list, group_type: GroupType):
        super().__init__(source_samples, group_type)

    def __repr__(self):
        pass

    def fill_comments(self):
        # Метод заполняет поле комментарии. коментарий - это число, которое показывает необходимость убрать выделяющийся
        # крайний результат или оставить его. Для каждой группы комментарии представлены для трех первый и трех
        # последних проб.
        for group in self:
            length = len(group)
            for a in range(0, 3):
                first_element = group[a].conc
                next_element = group[a + 1].conc
                penult_element = group[- 2].conc
                if penult_element > first_element:
                    min_val = round(((next_element - first_element) / (penult_element - first_element)), 2)
                    group[a].comment = min_val
            for b in range(int(length - 3), int(length)):
                last_element = group[b].conc
                second_element = group[2].conc
                penult_element = group[b - 1].conc
                if last_element > second_element:
                    max_val = round((last_element - penult_element) / (last_element - second_element), 2)
                    group[b].comment = max_val

    # Здесь начинаются методы, осуществляющие непосредственно статистическую обработку результатов. в общепринятой
    # практике это выполняется в прогремме Statistica.

    def find_degree_of_freedom(self):
        total_count = 0
        for group in self:
            total_count += len(group)
        df = total_count - 1
        return df

    # @staticmethod
    # В Statistica - effective size.
    def find_line_interaction_two_way(self, control_group_list: GroupedSamples, line_group_list: GroupedSamples):
        cont_f, cont_p = scipy.stats.f_oneway(*control_group_list.to_conc_lists())  # Для подсчета влияния каждого
        # фактора необходимо сгруппировать по факторам весь список проб
        cont_df = len(control_group_list.to_conc_lists())
        line_f, line_p = scipy.stats.f_oneway(*line_group_list.to_conc_lists())
        line_df = len(line_group_list.to_conc_lists())
        cxl_f, cxl_p = scipy.stats.f_oneway(*self.to_conc_lists())
        cxl_df = len(self.to_conc_lists())
        return cont_f, cont_p, cont_df, line_f, line_p, line_df, cxl_f, cxl_p, cxl_df

    @staticmethod
    def find_line_interaction_one_way(control_group_list: GroupedSamples):
        cont_f, cont_p = scipy.stats.f_oneway(*control_group_list.to_conc_lists())
        cont_df = len(control_group_list.to_conc_lists())
        return cont_f, cont_p, cont_df

    def find_weighted_mean(self):
        conc_array = self.to_conc_lists()
        averages = []
        for group in conc_array:
            averages.append(numpy.ma.average(group))
        return averages

    def find_standard_error(self):
        list_of_st_err = []
        for group in self.to_conc_lists():
            standard_error = scipy.stats.sem(group)
            list_of_st_err.append(standard_error)
        return list_of_st_err

    @staticmethod
    def find_differences_with_fisher(item1, item2):
        result = scipy.stats.f_oneway(item1, item2)
        return result


class Influence:
    # Класс с объектами, отображающими влияние линий.
    def __init__(self, name, f, p):
        self.name = name
        self.f = f
        self.p = p

    def __repr__(self):
        return self.name + '\t' + self.f + '\t' + self.p


class NamedGroup:
    # Класс с объектами-группами проб.
    def __init__(self, group, cont, line, number):
        self.group = group
        self.cont = cont
        self.line = line
        self.number = number

    def __repr__(self):
        return str(self.group) + '\t' + str(self.cont) + '\t' + str(self.line) + '\t' + str(self.number)


class AverageWithError:
    # Класс объектов с ошибками и средним.
    def __init__(self, group_number, average, error):
        self.group_number = group_number
        self.average = average
        self.error = error

    def __repr__(self):
        return str(self.group_number) + '\t' + str(self.average) + '\t' + str(self.error)


class LogicLayer:
    # Логическая составляющая интерфейса.
    sample_list = []

    def open_work_file(self):
        # Метод кнопки открытия файла с данныи, готовыми к статистической обработке. Возвращает набор строчек и полное
        # имя файла. В процессе работы заполняет поля "Комментарий".
        open_path = tk.askopenfilename()
        file_name = open_path
        samples = SampleList(file_name)
        if samples[1].line != 0:
            allsamples = GroupStatistics(samples, GroupType.Normal)
        else:
            allsamples = GroupStatistics(samples, GroupType.Control)
        allsamples.fill_comments()
        self.sample_list = []
        for supersample in allsamples:
            for sample in supersample:
                self.sample_list.append(sample)
        return self.sample_list, file_name

    @staticmethod
    def resume_processing(full_list):
        # Метод продолжения работы после указания всех проб, которые должны принять участие в статистической обработке.
        # Возвращает список, в который построчно записаны результаты статистической обработки.
        results = []
        samples = SampleListWithoutBads(full_list)
        if samples[1].line != 0:
            tempsamples = GroupStatistics(samples, GroupType.Normal)
        else:
            tempsamples = GroupStatistics(samples, GroupType.Control)

        degree_of_freedom = tempsamples.find_degree_of_freedom()
        df_result = 'degree of freedom = ' + str(degree_of_freedom)
        # Возвращает степень свободы.
        results.append(df_result)
        results.append('')

        results.append('Influence of factors:')
        # Возвращает влияние факторов "линия" и "эксперимент" и сочетания факторов.
        if samples[1].line != 0:
            cont_f, cont_p, cont_df, line_f, line_p, line_df, cxl_f, cxl_p, cxl_df = tempsamples.find_line_interaction_two_way \
                (GroupStatistics(samples, GroupType.Control), GroupStatistics(samples, GroupType.Line))
            results.append('control: F(' + str(cont_df) + ', ' + str(degree_of_freedom) + ')=' +
                           str(round(cont_f, 2)) + ' p=' + str(round(cont_p, 3)) + '\n' + 'line: F(' + str(line_df) +
                           ', ' + str(degree_of_freedom) + ')=' + str(round(line_f, 2)) + ' p=' +
                           str(round(line_p, 3)) + '\n' + 'cont x line: F(' + str(cxl_df) + ', ' +
                           str(degree_of_freedom) + ')=' + str(round(cxl_f, 2)) + ' p=' +
                           str(round(cxl_p, 3)))
        else:
            cont_f, cont_p, cont_df = tempsamples.find_line_interaction_one_way(GroupStatistics(samples, GroupType.Control))
            results.append('control: F(' + str(cont_df) + ', ' + str(degree_of_freedom)
                           + ')=' + str(round(cont_f, 2)) +
                           ' p=' + str(round(cont_p, 3)))

        results.append('')

        results.append('Groups:')
        # Возвращает пронумерованный список групп.
        index = 1
        for group in tempsamples:
            row_of_concs_in_group = ''
            for i in range(0, len(group)):
                row_of_concs_in_group = row_of_concs_in_group + str(group[i].conc) + '\t'
            if samples[1].line != 0:
                results.append(NamedGroup(index, group[0].control, group[0].line, row_of_concs_in_group))
            else:
                results.append(NamedGroup(index, group[0].control, '', row_of_concs_in_group))
            index += 1
        results.append('')

        results.append('Weighted means and st.errors')
        # Возвращает среднее взвешенное и ошибку среднего для каждой группы.
        results.append(AverageWithError('', 'mean', 'error'))
        averages = tempsamples.find_weighted_mean()
        list_of_st_err = tempsamples.find_standard_error()
        for i in range(0, len(tempsamples)):
            results.append(AverageWithError(i+1, round(averages[i], 3), round(list_of_st_err[i], 3)))
        results.append('')

        if samples[1].line != 0:
            results.append('Fisher analysis')
            # Возвращает результаты анализа-сравнения каждой группы с любой другой по Фишеру.
            row_1 = '\t'
            for index in range(0, len(tempsamples)):
                row_1 = row_1 + str(index+1) + '\t'
            results.append(row_1)
            conc_tempsamples = tempsamples.to_conc_lists()
            i = 1
            for index_1 in conc_tempsamples:
                row = str(i) + '\t'
                for index_2 in conc_tempsamples:
                    f, p = GroupStatistics.find_differences_with_fisher(index_1, index_2)
                    if p == 1.0:
                        p = 1
                    if p < 0.05:
                        row = row + '*' + str(round(p, 3)) + '*' + '\t'
                    else:
                        row = row + str(round(p, 3)) + '\t'
                results.append(row)
                i += 1

        return results

    @staticmethod
    def save_results_to_file(full_list):
        # Метод сохранения результата в текстовый файл построчно.
        save_path = tk.asksaveasfilename(filetypes=[('text files', '.txt'), ('all files', '.*')],
                                         initialfile='ANOVA_result.txt')
        file = open(save_path, 'w')
        for item in LogicLayer.resume_processing(full_list):
            file.write(str(item) + '\n')
        file.close()


class Interfacing:
    list_without_bads = []
    sample_list = []

    def __init__(self):
        self.logic = LogicLayer()
        root = tk.Tk()
        root.title('Statistic processing')
        # Создание основного окна.
        root.minsize(600, 400)
        # self.len, self.wieg = root.minsize()

        right_frame = tk.Frame(root)
        # Создание рамки справа в основном окне для группировки кнопок.
        self.open_button = tk.Button(right_frame, text='Open file', command=self.open_work_file)
        self.open_button.pack(side='top', fill='x')

        self.result_button = tk.Button(right_frame, text='Result', command=self.result_processing)
        self.result_button.pack(side='top', fill='x', pady=12)
        right_frame.pack(side='right', fill='y', pady=4, padx=2)

        self.left_frame = tk.Frame(root)
        # Создание рамки в левой части основного окна для группировки поля пути файла и заголовков.
        self.filename_entry = tk.Entry(self.left_frame)
        self.filename_entry.insert(0, 'Select file...')
        self.filename_entry.pack(side="top", fill="x", expand=False)

        self.header_text = tk.Label(self.left_frame, text='')
        self.header_text.pack(side="top", fill="x",)

        self.left_frame.pack(fill='both', side="left", expand=True, pady=4, padx=2)

        root.mainloop()

    def open_work_file(self):
        # Записывает путь до файла в поле пути.
        # try:
            self.sample_list, file_path_text = self.logic.open_work_file()
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.insert(0, file_path_text)

            # Generating all the sample pages and storing them in object field.
            self.pages_list = self.create_sample_elements_frame()
            self.pages_list[0].pack()
            self.active_page = self.pages_list[0]

            self.page_buttons_frame = self.create_page_buttons_frame()
            # Создание рамки в оснвном окне для группировки чек-боксов с пробами.
            self.page_buttons_frame.pack(side='bottom', pady=10)
        # except Exception:
        #     error_text = 'Wrong file'
        #     self.open_error_window(error_text)

    @staticmethod
    def split(source: list, chunk_size: int):
        # Разделение списка объектов по страницам. На каждой странице количество объектов равное chunk_size.
        full_result = []
        index = 0
        while True:
            result = source[index: index + chunk_size]
            if len(result) == 0:
                break
            full_result.append(result)
            index += chunk_size
        return full_result

    def create_sample_elements_frame(self):
        # Создание рамки для упорядочения чек-боксов и объектов.
        all_pages = []
        for result in Interfacing.split(self.sample_list, 12):
            samples_frame = tk.Frame(self.left_frame)
            tk.Label(samples_frame, text=" ").grid(column=0, row=0, padx=5, pady=2)
            tk.Label(samples_frame, text="Number").grid(column=1, row=0, padx=5, pady=2)
            tk.Label(samples_frame, text="Line").grid(column=2, row=0, padx=5, pady=2)
            tk.Label(samples_frame, text="Concentration").grid(column=3, row=0, padx=5, pady=2)
            tk.Label(samples_frame, text="Comment").grid(column=4, row=0, padx=5, pady=2)
            # Создание строки с заголовками.
            number_of_row = 1
            try:
                current_control_and_line = result[0].control + '_' + result[0].line
            except TypeError:
                current_control_and_line = result[0].control

            current_color = 'white'
            different_color = 'grey90'
            for element in result:
                var = tk.BooleanVar(value=True)
                f = functools.partial(self.check_sample, element=element, checked=var)
                check = tk.Checkbutton(samples_frame, text='', variable=var, onvalue=True, offvalue=False, command=f)
                check.select()  # Setting this settings of checkbox by default.
                check.grid(column=0, row=number_of_row)

                # Окрашивание строк таблицы
                try:
                    new_control_and_line = element.control + '_' + element.line
                except TypeError:
                    new_control_and_line = element.control
                if new_control_and_line == current_control_and_line:
                    color = current_color
                else:
                    color = different_color
                    current_color, different_color = different_color, current_color
                    current_control_and_line = new_control_and_line

                # Создание чек-боксов.

                number_box = tk.Entry(samples_frame)
                number_box.grid(column=1, row=number_of_row)
                number_box.delete(0, tk.END)
                number_box.insert(0, element.number)
                number_box.config(background=color)
                # Создание текстового поля для номера пробы.

                line_box = tk.Entry(samples_frame)
                line_box.grid(column=2, row=number_of_row)
                line_box.delete(0, tk.END)
                try:
                    line_box.insert(0, element.control + '_' + element.line)
                except TypeError:
                    line_box.insert(0, element.control)
                line_box.config(background=color)
                # Создание текстового поля для линии (разное влияние эксперимента) пробы.

                conc_box = tk.Entry(samples_frame)
                conc_box.grid(column=3, row=number_of_row)
                conc_box.delete(0, tk.END)
                conc_box.insert(0, element.conc)
                conc_box.config(background=color)
                # Создание текстового поля для линии (контроль\эксперимент) пробы.

                comment_box = tk.Entry(samples_frame)
                comment_box.grid(column=4, row=number_of_row)
                comment_box.delete(0, tk.END)
                comment_box.insert(0, element.comment)
                comment_box.config(background=color)
                # Создание текстового поля для комментария для пробы.

                number_of_row += 1

            all_pages.append(samples_frame)
        return all_pages

    @staticmethod
    def check_sample(element, checked):
        checked_value = checked.get()
        element.is_checked = checked_value
        # Наполнение списка из отмеченных чекбоксов.

    def create_page_buttons_frame(self):
        page_buttons_frame = tk.Frame(self.left_frame)
        # Создание рамки в основном окне для упорядочения кнопок страниц.
        for page_index in range(0, len(self.pages_list)):
            page_button = tk.Button(page_buttons_frame, text=str(page_index+1))
            f = functools.partial(self.click_page_button, page_index=page_index, clicked_button=page_button)
            page_button.config(command=f)
            # Изменение отображаемого списка объектов при нажатии на кнопку.
            page_button.pack(side='left', pady=4, padx=2)
            if page_index == 0:
                page_button.config(foreground="green")
                self.active_button = page_button
                # Изменение цвета кнопки при нажатии.
        return page_buttons_frame

    def click_page_button(self, page_index, clicked_button):
        # Switching pages.
        current_page = self.pages_list[page_index]
        self.active_page.pack_forget()
        current_page.pack()
        self.active_page = current_page
        # Changing button colors!
        clicked_button.config(foreground="green")
        self.active_button.config(foreground="black")
        self.active_button = clicked_button

    def result_processing(self):
        # Открытие окна с результатами.
        try:
            results = self.logic.resume_processing(self.sample_list)
            self.open_anova_results(results)
        except Exception:
             error_text = 'Wrong file'
             self.open_error_window(error_text)

    def open_anova_results(self, results):
        result = tk.Tk()
        result.title('ANOVA Results')
        # Создание окна с результатами.
        result.minsize(600, 400)

        right_frame = tk.Frame(result)
        # Создание рамки в окне с результатами для группировки кнопок.
        f = functools.partial(self.logic.save_results_to_file, full_list=self.sample_list)
        save_button = tk.Button(right_frame, text='Save', command=f)
        save_button.pack(side='bottom', fill='x')
        right_frame.pack(side='right', fill='y', pady=4, padx=2)

        result_left_frame = tk.Frame(result)
        self.result_text_box = tk.Text(result_left_frame, wrap=tk.WORD)
        self.result_text_box.pack(side='top', fill="both", expand=True)
        self.result_text_box.delete(1.0, tk.END)
        for res in results:
            self.result_text_box.insert(tk.END, str(res) + '\n')
        self.result_text_box.config(state=tk.DISABLED)

        scrollbar_1 = tk.Scrollbar(self.result_text_box)
        scrollbar_1.pack(side='right', fill='both')
        scrollbar_1['command'] = self.result_text_box.yview
        self.result_text_box['yscrollcommand'] = scrollbar_1.set

        result_left_frame.pack(fill='both', side="left", expand=True, pady=4, padx=2)

        result.mainloop()

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
