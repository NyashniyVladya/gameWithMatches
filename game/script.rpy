
init python:

    from threading import Lock
    from random import Random
    from __builtin__ import (
        map as fixedMap,
        min as fixMin,
        all as fixAll
    )

    class ReloadException(Exception):
        u"""
        Обёртка, для обработки перезагрузки.
        """

    class ExitException(Exception):
        u"""
        Обёртка, для обработки выхода.
        """

    class LogicControl(Random, NoRollback):

        symb_replace_mapping = {
            "+-": '-',
            "-+": '-',
            "++": '+',
            "--": '+',

        }

        def __init__(self, hard=False):
            super(LogicControl, self).__init__()
            self.hard_mode = hard
            (
                self.true_expr,
                self.false_expr
            ) = (
                self.generate_false_expression()
            )
            self.disp = MatchGameTable(self.false_expr, "match.png")
            self.steps = self.calculate_steps() * 2
            self.update_status()

        def start_cycle(self):
            renpy.show("matchGameDisp", what=self.disp)
            self.disp.return_pos_all_children()
            renpy.show(
                "matchGameButtonsBox",
                what=VBox(
                    renpy.display.behavior.TextButton(
                        u"Выход",
                        clicked=Function(renpy.end_interaction, "exit"),
                    ),
                    renpy.display.behavior.TextButton(
                        u"Другое задание",
                        clicked=Function(renpy.end_interaction, "reload"),
                    ),
                    renpy.display.behavior.TextButton(
                        u"Сделать правильный ход",
                        clicked=Function(self.auto_step),
                    ),
                    align=(.99, .01)
                )
            )
            while True:
                self.steps -= self.disp.interact_handler()
                self.update_status()
                if self.is_solved or (self.steps <= 0):
                    return self.is_solved

        def hide(self):
            for i in ("ButtonsBox", "Disp", "StatusText"):
                renpy.hide("matchGame{0}".format(i))

        def get_not_right_elements(self):
            u"""
            Возвращает элементы, которые находятся не на своих местах.
            """
            assert (len(self.expression_now) == len(self.true_expr))
            _tokens = MatchGameTable.token_mapping
            _step_counter = 0

            _not_right_drops = {
                '0': [],
                '1': []
            }
            for order_num, exprs in enumerate(
                zip(self.disp.get_bit_masks(), self.true_expr)
            ):
                current_mask, true_token = exprs
                true_mask = bin(_tokens[true_token])[2:]
                while len(true_mask) < len(current_mask):
                    true_mask = '0' + true_mask
                for current_bit, true_bit, element_name in zip(
                    current_mask,
                    true_mask,
                    MatchGameTable.elements_names
                ):
                    if current_bit != true_bit:
                        _not_right_drops[current_bit].append(
                            self.disp.get_drag_for_name_and_order(
                                order_num,
                                element_name
                            )
                        )
            return _not_right_drops

        def auto_step(self):
            u"""
            Делает правильный ход, приближающий к решению.
            """
            if self.steps < 3:
                return
            if self.disp._move_lock.locked():
                return
            elements = self.get_not_right_elements()
            try:
                drag = self.choice(elements['1'])
                drop = self.choice(elements['0'])
            except IndexError:
                return
            self.disp.drop_action(drag, drop)
            renpy.end_interaction("skip")

        def update_status(self):
            self.expression_now, self.is_solved = self.disp.current_value()
            self.status = (
                u"Решено." if self.is_solved else u"Не решено."
            )
            renpy.show(
                "matchGameStatusText",
                what=Text(
                    u"\n".join(
                        (
                            self.expression_now.replace(u"==", u"="),
                            self.status,
                            u"Осталось ходов: {0}.".format(self.steps),
                            u"Ответ: {0}. (В релизе этого не будет).".format(
                                self.true_expr.replace(u"==", u"=")
                            )
                        )
                    ),
                    size=50,
                    align=(.01, .01)
                )
            )

        def calculate_steps(self):
            u"""
            Возвращает минимальное количество шагов, необходимое, 
            для разрешения текущей ситуации.
            """
            return len(self.get_not_right_elements()['1'])

        def generate_true_expression(self):
            u"""
            Создаёт случайное верное равенство.
            """
            string = str(self.randint(1, 99))
            max_val = (self.randint(2, 4) if self.hard_mode else 1)
            for i in xrange(max_val):
                string += self.choice("+-*")
                string += str(self.randint(-99, 99))
            for shabl, repl in self.symb_replace_mapping.iteritems():
                string = string.replace(shabl, repl)
            solution = eval(string)
            string += "="
            string += str(solution)
            return string

        def generate_false_expression(self):
            u"""
            Создаёт неверное равенство, которое будет целью задачи.
            Возвращате массив формата:
            (
                Верное равенство,
                Неверное, произведённое из верного
            )
            """
            expr = self.generate_true_expression()
            temp_str = ""
            parts = []
            num_array = ""
            for i in (expr + '\0'):
                if i.isdigit():
                    temp_str += i
                    num_array += i
                else:
                    if temp_str:
                        parts.append(temp_str)
                        temp_str = ""
                    if i not in "sn\0":
                        parts.append(i)

            num_array = self.transform_num_array(num_array)
            if self.hard_mode:
                num_array = self.shuffle_string(num_array)
            final_expr = ""
            for part in parts:
                if part.isdigit():
                    crop = len(part)
                    while num_array.startswith('0') and (len(num_array) > 1):
                        num_array = self.shuffle_string(num_array)
                    final_expr += num_array[:crop]
                    num_array = num_array[crop:]
                else:
                    final_expr += part
            if eval(final_expr.replace('=', "==")):
                return self.generate_false_expression()
            return (expr, final_expr)

        def shuffle_string(self, string):
            str_data = list(string)
            self.shuffle(str_data)
            return "".join(str_data)

        def transform_num_array(self, expr):
            u"""
            Изменяет последовательность, таким образом, 
            чтобы количество спичек осталось прежним, при изменении значений.
            """
            _offset_first = (1 if self.hard_mode else 5)
            while True:
                offset = 0
                _first_offset = self.randint(
                    (_offset_first * -1),
                    _offset_first
                )
                restart_counter = 0
                work_expr = expr
                while True:
                    restart_counter += 1
                    if restart_counter > 8:
                        break
                    token = self.choice(work_expr)
                    transform, balance_offset = self.get_transform_variant(
                        token,
                        (offset or _first_offset)
                    )
                    _first_offset = 0
                    balance_offset *= work_expr.count(token)
                    offset += balance_offset
                    work_expr = work_expr.replace(token, transform)
                    if not offset:
                        return work_expr

        def get_transform_variant(self, token, corrector=0):
            u"""
            Возвращает возможный вариант трансформации, для токена, 
            на основе сходства двоичного маппинга.

            Формат возврата:
                (
                    новый токен, 
                    значение смещения баланса
                )

            :corrector:
                < 0:
                    Нужен токен, с меньшим количеством спичек.
                    Будет возвращено положительное число.
                > 0: 
                    Логика инвертируется.
                0:
                    Смещение не требуется. 
            """
            _dct = MatchGameTable.quantitative_mapping
            match_in_token = _dct[token]
            variants = [(k, v) for k, v in _dct.iteritems() if k.isdigit()]
            self.shuffle(variants)
            while True:
                need_token_match = match_in_token + corrector
                for tok, match_len in variants:
                    if (tok != token) and (match_len == need_token_match):
                        return (tok, (corrector * -1))
                corrector += self.choice((1, -1))

    class MatchGameTable(DragGroup, NoRollback):
        token_mapping = {
            '0': 0b111111000000,
            '1': 0b11000000000,
            '2': 0b110110100000,
            '3': 0b111100100000,
            '4': 0b11001100000,
            '5': 0b101101100000,
            '6': 0b101111100000,
            '7': 0b111001000000,
            '8': 0b111111100000,
            '9': 0b111101100000,
            '+': 0b110000,
            '-': 0b100000,
            '*': 0b1100,
            '/': 0b100,
            '=': 0b11,
            'n': 0b111,
            's': 0b0
        }
        reverced_mapping = {v: k for k, v in token_mapping.iteritems()}
        replace_mapping = {
            'n': "!=",
            '=': "==",
            's': " "
        }
        quantitative_mapping = {
            k: bin(v).count('1') for k, v in token_mapping.iteritems()
        }
        elements_names = "abcdefghijkl"
        segment_len = len(elements_names)

        def __init__(self, expression, *match_pics):

            super(MatchGameTable, self).__init__()
            self.tokens_len = len(expression)
            self.base_offset = 1.5
            self._move_lock = Lock()
            self.self_layer = "master"
            for ind, token in enumerate(str(expression)):
                for name, draggable in zip(
                    self.elements_names,
                    self._get_mapping_from_int(token)
                ):
                    pic = renpy.random.choice(match_pics)
                    self.add(
                        MatchObject(
                            match_pic=pic,
                            draggable=draggable,
                            drag_name=name,
                            order_num=ind,
                            zoom=self.calculate_zoom(pic),
                            base_offset=self.base_offset
                        )
                    )

        def visit(self):
            return self.children

        def calculate_zoom(self, pic):
            square_size = renpy.render(
                Transform(pic, rotate=45),
                0, 0, 0, 0
            ).get_size()[0]
            width = square_size * self.base_offset * (self.tokens_len + 1)
            height = square_size * 2
            xzoom = float(config.screen_width) / width
            yzoom = float(config.screen_height) / height
            return fixMin(xzoom, yzoom)

        def interact_handler(self):
            u"""
            Обработчик значений, возвращаемых в результате интеракта.
            """
            ui_return_val = ui.interact()
            if ui_return_val == "skip":
                return 3
            if ui_return_val == "reload":
                raise ReloadException()
            if ui_return_val == "exit":
                raise ExitException()
            with self._move_lock:
                drops = tuple(self.__get_best_drops(ui_return_val))
                if len(drops) == 1:
                    drop = drops[0][-1]
                else:
                    drop = renpy.display_menu(drops)
            self.drop_action(ui_return_val, drop)
            return 1

        def drop_action(self, drags_list, drop):
            u"""
            Меняет местами положения объектов.
            """
            if not hasattr(drags_list, "__iter__"):
                drags_list = [drags_list]
            for drag in drags_list:
                (
                    drag.drag_name,
                    drop.drag_name,
                    drag.order_num,
                    drop.order_num,
                ) = (
                    drop.drag_name,
                    drag.drag_name,
                    drop.order_num,
                    drag.order_num
                )
                drag.update_setting_from_name()
                drop.update_setting_from_name()

            drop.move_to_drag_coors(0)
            for drag in drags_list:
                drag.move_to_drag_coors()

        def __get_best_drops(self, drags_list):
            u"""
            Возвращает генератор меню, для выбора места сброса.
            """
            max_overlap = 0
            overlaps = []
            for d in drags_list:
                r1 = (d.x, d.y, d.w, d.h)
                for c in self.children:
                    if not c.droppable:
                        continue
                    r2 = (c.x, c.y, c.w, c.h)
                    overlap = c.rndInt(
                        renpy.display.dragdrop.rect_overlap_area(r1, r2)
                    )
                    overlaps.append((overlap, c))
                    if overlap > max_overlap:
                        max_overlap = overlap
            for overlap, drop in overlaps:
                if overlap == max_overlap:
                    yield (drop.corner, drop)

        def _get_mapping_from_int(self, token):
            u"""
            Принимает токен.

            Возвращает генератор булевых значений,
            где каждое из них последоватеньно определяет состояние элементов.
            """
            token_map = bin(self.token_mapping[token])[2:]
            for i in xrange((self.segment_len - len(token_map))):
                yield False
            for int_bool in token_map:
                yield bool(int(int_bool, 2))

        def __sorted_algorithm(self, drag):
            base_value = drag.order_num * self.segment_len
            second_value = self.elements_names.index(drag.drag_name)
            return base_value + second_value

        def get_drag_for_name_and_order(self, order, name):
            for drag in self.get_children():
                if (drag.order_num == order) and (drag.drag_name == name):
                    return drag
            raise Exception(u"Элемент {0}{1} не найден.".format(order, name))

        def current_value(self):
            u"""
            Вычисляет текущее выражение, на основе положений элементов.

            Возвращает кортеж, где первый элемент - строка выражения,
            а второй - булевое, определяющее, решено ли оно.
            """
            result = ""
            for binary_key in self.get_bit_masks():
                decimal_key = int(binary_key, 2)
                preresult = self.reverced_mapping.get(decimal_key, '?')
                result += self.replace_mapping.get(preresult, preresult)

            if isinstance(result, str):
                result = result.encode("utf-8", "ignore")
            result = result.strip()
            is_right = False
            if u'?' not in result:
                if u"==" in result:
                    try:
                        if eval(result):
                            is_right = True
                    except SyntaxError:
                        pass
                    except ZeroDivisionError:
                        pass
            return (result, is_right)

        def get_bit_masks(self):
            u"""
            Генератор.
            Возвращает бинарное состояние каждого элемента.
            """
            temp_val = ""
            for ind, drag in enumerate(
                sorted(self.get_children(), key=self.__sorted_algorithm)
            ):
                ind += 1
                temp_val += str(int(drag.draggable))
                if not (ind % self.segment_len):
                    yield temp_val
                    temp_val = ""

        def return_pos_all_children(self):
            u"""
            Перемещает все спички на их изначальные координаты.
            """
            for i in self.get_children():
                i.move_to_drag_coors()

    class MatchObject(Drag, NoRollback):

        u"""
        Объект спички.
        Изначальное изображение должно быть горизонтальным.
        """

        pos_mapping = {
            "a": "(({s} * .5), 0)",
            "b": "({s}, ({s} * .5))",
            "c": "({s}, ({s} * 1.5))",
            "d": "(({s} * .5), ({s} * 2))",
            "e": "(0, ({s} * 1.5))",
            "f": "(0, ({s} * .5))",
            "g": "(({s} * .5), {s})",
            "h": "(({s} * .5), {s})",
            "i": "(({s} * .5), {s})",
            "j": "(({s} * .5), {s})",
            "k": "(({s} * .5), ({s} * 1.2))",
            "l": "(({s} * .5), ({s} * .8))",
        }
        conformity_mapping = (
            (u"Вертикальное расположение.", (90, 270), "fbech"),
            (u"Диагональ. Наклон влево.", (45, 225), "i"),
            (u"Горизонтальное расположение.", (0, 180), "agdkl"),
            (u"Диагональ. Наклон вправо.", (315, 135), "j")
        )

        def __init__(
            self,
            drag_name,
            match_pic,
            draggable=False,
            order_num=0,
            zoom=1.,
            base_offset=1.,
            **prop
        ):
            draggable = bool(draggable)
            for corner_name, rotates, drag_names in self.conformity_mapping:
                if drag_name in drag_names:
                    set_rotate = renpy.random.choice(rotates)
                    self.corner = corner_name
            param = {
                "d": Transform(
                    match_pic,
                    rotate=set_rotate,
                    alpha=(1. if draggable else .0),
                    zoom=zoom
                ),
                "draggable": draggable,
                "droppable": (not draggable),
                "drag_name": drag_name,
                "dragged": self.return_dragged
            }
            param.update(prop)
            super(MatchObject, self).__init__(**param)
            self.order_num = order_num
            self.base_offset = base_offset
            self.xsize, self.ysize = fixedMap(
                self.rndInt,
                renpy.render(self, 0, 0, 0, 0).get_size()
            )
            self.scatter_matches()
            self.update_setting_from_name()

        def update_corner(self):
            u"""
            Обновляет угол, вычисляя его, из имени объекта.
            """
            for corner_name, rotates, drag_names in self.conformity_mapping:
                if self.drag_name in drag_names:
                    param = self.child.kwargs
                    param["rotate"] = renpy.random.choice(rotates)
                    self.set_child(Transform(self.child.child, **param))
                    self.corner = corner_name
                    return

        def visit(self):
            return [self.child]

        def return_dragged(self, drags_list, drop):

            if drop and (not self.drag_group._move_lock.locked()):
                return drags_list
            for drag in drags_list:
                drag.move_to_drag_coors()
            return

        def scatter_matches(self, time=0):
            u"""
            Устанавливает случайные координаты спички. Для эффекта раскидывания.
            """
            x, y = fixedMap(
                lambda a: self.rndInt((renpy.random.random() * a)),
                (config.screen_width, config.screen_height)
            )
            self.snap(x, y, time)

        def move_to_drag_coors(self, time=-1):
            u"""
            Перемещает спичку на предустановленные координаты.
            """
            if time < 0:
                time = renpy.random.random() * .5
            self.snap(self.base_x, self.base_y, time)

        def update_setting_from_name(self):
            u"""
            Устанавливает координаты и угол спички, из её имени.
            """

            x, y = fixedMap(
                self.rndInt,
                eval(self.pos_mapping[self.drag_name].format(s=self.xsize))
            )
            self.base_y = y + self.rndInt(
                ((config.screen_height * .5) - (self.ysize * 1.5))
            )
            self.base_x = x + self.rndInt(
                (self.xsize * self.base_offset * self.order_num)
            )
            self.update_corner()

        def rndInt(self, val):
            return int(round(float(val)))

    def startMatchGame(roundCount=3):
        u"""
        Запускает игру из трёх раундов.
        Возвращает генератор, итерировать результат, через all.
        """
        for i in xrange(roundCount):
            i += 1
            try:
                try_counter = 0
                while True:
                    try_counter += 1
                    renpy.say(
                        None,
                        u"{0} раунд. Попытка №{1}".format(i, try_counter)
                    )
                    gameLogic = LogicControl(
                        renpy.display_menu(
                            (
                                (u"Юзаем хардмод", True),
                                (u"Не, не, не. И так всё нормально.", False),
                            )
                        )
                    )
                    try:
                        result = gameLogic.start_cycle()
                    except ReloadException:
                        continue
                    if result:
                        yield result
                        break
                    raise ExitException()
            except ExitException:
                yield False
                break
            finally:
                try:
                    gameLogic.hide()
                except:
                    pass

label start:
    "Правила таковы: Количество ходов, которые можно сделать, равно минимуму ходов, для правильного решения, помноженному на 2."
    "Ваш обычный ход отнимает один ход. Так же Вы можете воспользоваться подсказкой - компьютер сделает за Вас гарантированно верный ход. Это отнимает три хода."
    "Используйте её умело, т.к. может случиться, что, зная решение, у Вас не останется ходов."
    if fixAll(startMatchGame()):
        "Молодец."
    else:
        "Не молодец."
    return
