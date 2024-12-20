import random
import time
import asyncio
import curses
from itertools import cycle
from pathlib import Path


def draw(canvas):
    canvas.border()
    height, width = curses.window.getmaxyx(canvas)
    middle_row = height // 2
    middle_column = width // 2

    curses.curs_set(False)
    coroutines = [
        blink(
            canvas,
            row=random.randint(1, height - 2),
            column=random.randint(1, width - 2),
            symbol=random.choice('+*.:')
        )
        for _ in range(100)
    ]
    coroutines += [
        fire(
            canvas,
            start_row=middle_row,
            start_column=middle_column,
            rows_speed=-0.3,
            columns_speed=0
        )

    ]

    coroutines += [
        animate_spaceship(canvas, start_row=middle_row, start_column=middle_column)
    ]
    while True:
        canvas.refresh()
        time.sleep(0.1)
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(random.randint(1, 20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(random.randint(1, 3)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(random.randint(1, 5)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(random.randint(1, 3)):
            await asyncio.sleep(0)


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""
    SPACE_KEY_CODE = 32
    LEFT_KEY_CODE = 260
    RIGHT_KEY_CODE = 261
    UP_KEY_CODE = 259
    DOWN_KEY_CODE = 258

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -5

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 5

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 5

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -5

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def animate_spaceship(canvas, start_row, start_column):
    folder_path = Path("rocket_frame")

    row, column = start_row, start_column

    contents = []
    for file_path in folder_path.iterdir():
        if file_path.is_file():
            with file_path.open('r', encoding='utf-8') as file:
                content = file.read()
                contents.append(content)

    for item in cycle(contents):
        canvas.nodelay(True)
        rows_direction, columns_direction, space_pressed = read_controls(canvas)

        row += rows_direction
        column += columns_direction

        frame_row, frame_column = get_frame_size(item)

        max_rows, max_columns = canvas.getmaxyx()

        if row + frame_row >= max_rows:
            row = max_rows - frame_row
        if row <= 0:
            row = 0
        if column <= 0:
            column = 0
        if column + frame_column >= max_columns:
            column = max_columns - frame_column

        draw_frame(canvas, row, column, item)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, item, negative=True)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
