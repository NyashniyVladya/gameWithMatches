
init python:

    from __builtin__ import map as fixedMap
    from threading import Lock
    from random import Random

    class LogicControl(Random):

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
                self.false_expr,
                self.steps
            ) = (
                self.generate_false_expression()
            )
            self.disp = MatchGameTable(self.false_expr)
            self.update_status()

        def start_cycle(self):
            self.disp.show()
            self.disp.return_pos_all_children()
            while True:
                self.disp.drop_action(ui.interact())
                self.steps -= 1
                self.update_status()
                if self.is_solved or (self.steps <= 0):
                    return self.is_solved

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

        def calculate_steps(self, first_expr, second_expr):
            u"""
            Принимает два выражения, возвращает количество "шагов", 
            для трансформации одного в другое.
            """
            assert (len(first_expr) == len(second_expr))
            _tokens = MatchGameTable.token_mapping
            _step_counter = 0
            for tok1, tok2 in zip(first_expr, second_expr):
                xor_result = _tokens[tok1] ^ _tokens[tok2]
                _step_counter += bin(xor_result).count('1')
            return _step_counter

        def generate_true_expression(self):
            u"""
            Создаёт случайное верное равенство.
            """
            string = str(self.randint(1, 99))
            for i in xrange(self.randint(1, (3 if self.hard_mode else 2))):
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
                Неверное произведённое из верного,
                Количество "шагов".
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
            num_array = list(num_array)
            if self.hard_mode:
                self.shuffle(num_array)
            while num_array[0] == '0':
                self.shuffle(num_array)
            num_array = "".join(num_array)
            final_expr = ""
            for part in parts:
                if part.isdigit():
                    crop = len(part)
                    final_expr += num_array[:crop]
                    num_array = num_array[crop:]
                else:
                    final_expr += part
            if eval(final_expr.replace('=', "==")):
                return self.generate_false_expression()
            return (expr, final_expr, self.calculate_steps(expr, final_expr))

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

    class MatchGameTable(DragGroup):
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

        def __init__(self, expression, match_pic="match.png"):

            super(MatchGameTable, self).__init__()
            self.tokens_len = len(expression)
            self.base_offset = 1.3
            self._move_lock = Lock()
            self.self_layer = "master"
            _zoom = self.calculate_zoom(match_pic)
            for ind, token in enumerate(str(expression)):
                for name, draggable in zip(
                    self.elements_names,
                    self._get_mapping_from_int(token)
                ):
                    self.add(
                        MatchObject(
                            match_pic=match_pic,
                            draggable=draggable,
                            drag_name=name,
                            order_num=ind,
                            zoom=_zoom,
                            base_offset=self.base_offset
                        )
                    )

        def calculate_zoom(self, pic):
            square_size = renpy.render(
                Transform(pic, rotate=45),
                0, 0, 0, 0
            ).get_size()[0]
            width = square_size * self.base_offset * (self.tokens_len + 1)
            height = square_size * 2
            xzoom = float(config.screen_width) / width
            yzoom = float(config.screen_height) / height
            return min(xzoom, yzoom)

        def show(self):
            ui.layer(self.self_layer)
            ui.add(self)
            ui.close()

        def hide(self):
            ui.layer(self.self_layer)
            ui.remove(self)
            ui.close()

        def drop_action(self, drags_list):
            u"""
            Определяет оптимальный дроп и "сбрасывает" туда объект.
            Если вариантов несколько - спрашивает.

            Вызывать извне интеракта.
            """
            with self._move_lock:
                drops = tuple(self.__get_best_drops(drags_list))
                if len(drops) == 1:
                    drop = drops[0][-1]
                else:
                    drop = renpy.display_menu(drops)
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

        def current_value(self):
            u"""
            Вычисляет текущее выражение, на основе положений элементов.

            Возвращает кортеж, где первый элемент - строка выражения,
            а второй - булевое, определяющее, решено ли оно.
            """
            temp_val = ""
            result = ""
            for ind, drag in enumerate(
                sorted(self.get_children(), key=self.__sorted_algorithm)
            ):
                ind += 1
                temp_val += str(int(drag.draggable))
                if (ind % self.segment_len) == 0:
                    temp_val = int(temp_val, 2)
                    preresult = self.reverced_mapping.get(temp_val, '?')
                    result += self.replace_mapping.get(preresult, preresult)
                    temp_val = ""
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

        def return_pos_all_children(self):
            u"""
            Перемещает все спички на их изначальные координаты.
            """
            for i in self.get_children():
                i.move_to_drag_coors()

    class MatchObject(Drag):

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
                    alpha=(1. if draggable else .05),
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

label start:
    menu:
        "Юзаем хардмод?"
        "Да!":
            $ _val = True
        "Не, не, не. И так всё нормально.":
            $ _val = False
    python:
        gameLogic = LogicControl(_val)
        result = gameLogic.start_cycle()
    if result:
        "Молодец!"
    else:
        "Не молодец."
    return
