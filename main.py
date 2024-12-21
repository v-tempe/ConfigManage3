import argparse  # Импортируем модуль для работы с аргументами командной строки
import sys  # Импортируем модуль для работы с системными вызовами
import re  # Импортируем модуль для работы с регулярными выражениями

import yaml


# Функция для вычисления префиксного выражения
def evaluate_prefix(expression, constants):
    # Убираем квадратные скобки и разбиваем строку на токены
    tokens = expression.strip('![]').split()
    stack = []  # Стек для хранения операндов
    i = len(tokens) - 1  # Индекс для перебора токенов (начинаем с конца)

    while i >= 0:
        token = tokens[i]  # Получаем текущий токен
        if token.isdigit():  # Если токен - число
            stack.append(int(token))  # Добавляем его в стек как целое число
        elif token in constants:  # Если токен - константа
            stack.append(constants[token])  # Добавляем значение константы в стек
        elif token == '+':  # Если токен - операция сложения
            if len(stack) < 2:  # Проверяем, достаточно ли операндов
                raise ValueError("Недостаточно операндов для выполнения операции.")
            a = stack.pop()  # Извлекаем первый операнд
            b = stack.pop()  # Извлекаем второй операнд
            stack.append(a + b)  # Выполняем сложение и помещаем результат в стек
        elif token == '-':  # Если токен - операция вычитания
            if len(stack) < 2:
                raise ValueError("Недостаточно операндов для выполнения операции.")
            a = stack.pop()  # Извлекаем первый операнд
            b = stack.pop()  # Извлекаем второй операнд
            stack.append(a - b)  # Выполняем вычитание и помещаем результат в стек
        elif token == '*':  # Если токен - операция умножения
            if len(stack) < 2:
                raise ValueError("Недостаточно операндов для выполнения операции.")
            a = stack.pop()  # Извлекаем первый операнд
            b = stack.pop()  # Извлекаем второй операнд
            stack.append(a * b)  # Выполняем умножение и помещаем результат в стек
        elif token == '/':  # Если токен - операция деления
            if len(stack) < 2:
                raise ValueError("Недостаточно операндов для выполнения операции.")
            a = stack.pop()  # Извлекаем первый операнд
            b = stack.pop()  # Извлекаем второй операнд
            stack.append(a / b)  # Выполняем деление и помещаем результат в стек
        elif token == 'chr':  # Если токен - операция взятия символа по его коду
            if len(stack) < 1:
                raise ValueError("Недостаточно операндов для операции pow.")
            num = stack.pop()  # Извлекаем операнд
            stack.append(chr(num))  # Выполняем возведение в степень и помещаем результат в стек
        else:  # Если токен не распознан
            raise ValueError(f"Неизвестный токен: {token}")

        i -= 1  # Переходим к следующему токену (в обратном порядке)

    if len(stack) != 1:  # Проверяем, что в стеке остался только один результат
        raise ValueError("Ошибка в выражении")

    return stack[0]  # Возвращаем результат вычисления


# Функция для удаления комментариев
def remove_comments(text):
    # Удаляем многострочные комментарии, заключенные в |# #|
    text = re.sub(r'\|#.*?#\|', '', text, flags=re.DOTALL)
    # Возвращаем текст без пробелов в начале и в конце
    return text.strip()


# Функция для парсинга объявления константы
def parse_constants(text):
    constants = {}  # Словарь для хранения найденных констант
    remaining_lines = []  # Список для хранения строк, не являющихся константами    

    # Проходим по каждой строке входного текста
    for line in text.splitlines():
        line = line.strip()  # Убираем лишние пробелы в начале и конце строки        

        # Проверяем, начинается ли строка с объявления константы
        if line.startswith("def ") and ':=' in line and line.endswith(';'):
            line = line[4:-1]
            name, expression = line.split(':=', 1)  # Разделяем на имя и выражение
            name = name.strip()  # Убираем лишние пробелы
            expression = expression.strip()  # Убираем лишние пробелы

            # Проверяем, является ли выражение префиксным
            if expression.startswith('![') and expression.endswith(']'):
                try:
                    # Вычисляем значение префиксного выражения
                    value = evaluate_prefix(expression, constants)
                    constants[name] = value  # Сохраняем результат в словарь констант
                except ValueError as e:
                    raise ValueError(f"Ошибка при вычислении выражения '{expression}': {e}")
            else:
                # Проверяем, является ли значением числом или строкой
                if expression.startswith('"') and expression.endswith('"'):
                    constants[name] = expression[1:-1]  # Убираем кавычки для строк
                else:
                    match = re.match(r"(\d+)", expression)  # Проверяем, является ли значением числом
                    if match:
                        constants[name] = int(
                            match.group(1))  # Сохраняем константу в словарь, преобразуя значение в целое число
                    else:
                        raise ValueError(f"Неверный формат константы: {line}")
        else:
            remaining_lines.append(
                line)  # Если строка не является константой, добавляем ее в список оставшихся строк

    return constants, "\n".join(remaining_lines)  # Возвращаем словарь констант и оставшийся текст в виде строки


# Функция для парсинга словаря
def parse_dict(text, constants):
    text = text.strip('\n')
    if not text.startswith('table(') or not text.endswith(')'):
        raise ValueError("Неверный формат словаря: должен начинаться с 'table(' и заканчиваться ')'")

    # Убираем 'table(' и ')' и лишние пробелы
    text = text[6:-1].strip()
    result = {}  # Словарь для хранения пар ключ-значение    
    buffer = ""  # Буфер для хранения текущей пары ключ-значение
    depth = 0  # Переменная для отслеживания вложенности

    for char in text:
        if char == ',' and depth == 0:  # Если встречаем запятую и глубина вложенности равна нулю
            if buffer.strip():  # Если буфер не пустой
                key_value = buffer.split('=>', 1)  # Разделяем на ключ и значение
                if len(key_value) != 2:  # Проверяем, что пара состоит из ключа и значения
                    raise ValueError(f"Неверный формат пары: {buffer}")
                key = key_value[0].strip()  # Извлекаем и обрезаем ключ
                value = key_value[1].strip()  # Извлекаем и обрезаем значение

                # Обработка значения
                if value.isdigit():  # Если значение - число
                    result[key] = int(value)  # Добавляем как целое
                elif value.startswith('"') and value.endswith('"'):  # Если значение - строка
                    result[key] = value[1:-1]  # Убираем кавычки
                elif value in constants:  # Если значение - константа
                    result[key] = constants[value]  # Добавляем ее значение
                else:
                    raise ValueError(f"Неизвестное значение: {value}")

                buffer = ""  # Очищаем буфер
        else:
            buffer += char  # Добавляем символ в буфер
            if char == '{':  # Увеличиваем глубину при встрече открывающей скобки
                depth += 1
            elif char == '}':  # Уменьшаем глубину при встрече закрывающей скобки
                depth -= 1

    # Обрабатываем последний элемент
    if buffer.strip():
        key_value = buffer.split('=>', 1)
        if len(key_value) != 2:
            raise ValueError(f"Неверный формат пары: {buffer}")
        key = key_value[0].strip()
        value = key_value[1].strip()

        if value.isdigit():
            result[key] = int(value)
        elif value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1]  # Убираем кавычки
        elif value in constants:
            result[key] = constants[value]
        else:
            raise ValueError(f"Неизвестное значение: {value}")

    return result  # Возвращаем собранный словарь


if __name__ == "__main__":  # Проверяем, что скрипт запускается напрямую

    input_file = input("Введите путь ко входном файлу: ")
    #input_file = "input_file.txt"
    output_file = "output_file.yaml"

    try:
        # Шаг 1. Чтение файла
        with open(input_file, 'r') as f:
            raw_text = f.read()  # Читаем содержимое файла
        # Шаг 2. Убираем комментарии
        cleaned_text = remove_comments(raw_text)

        # Шаг 3. Парсим константы
        constants, remaining_text = parse_constants(cleaned_text)

        # Шаг 4. Парсим словари
        parsed_data = parse_dict(remaining_text, constants)

        # Шаг 5. Преобразуем данные в XML
        xml_output = to_yaml(constants, parsed_data)  # Объединяем константы и распарсенные данные в XML

        # Записываем константы в выходной файл
        with open(output_file, 'w') as f:
            for const in constants:
                print(f"{const}: {constants[const]}", file=f)
        # Записываем словари в выходной файл
        with open(output_file, 'a') as f:
            print(f"table:", file=f)
            for pd in parsed_data:
                print(f"  {pd}: {parsed_data[pd]}", file=f)
    except Exception as e:  # Обработка исключений
        print(f"Ошибка: {e}", file=sys.stderr)  # Выводим сообщение об ошибке в стандартный поток ошибок
        sys.exit(1)  # Завершаем программу с кодом ошибки 1
