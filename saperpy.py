"""
Игра "Сапер" на PyQt5
"""

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import random
import time

LEVELS = (
    (8, 10),
    (16, 40),
    (24, 99)
)

IMG_BOMB = QImage('./images/bomb.png')
IMG_CLOCK = QImage('./images/clock.png')
IMG_START = QImage('./images/rocket.png')
IMG_FLAG = QImage('./images/flag.png')

STATUS_READY = 0
STATUS_PLAY = 1
STATUS_FAILED = 2
STATUS_SUCCESS = 3

STATUS_ICONS = {
    STATUS_READY: "./images/plus.png",
    STATUS_PLAY: "./images/smiley.png",
    STATUS_FAILED: "./images/cross.png",
    STATUS_SUCCESS: "./images/smiley-lol.png",
}


class Cell(QWidget):
    """
    Клетка игрового поля
    """
    expandable = pyqtSignal(int, int)
    accorded = pyqtSignal(int, int)
    clicked = pyqtSignal()
    flagged = pyqtSignal(bool)
    game_over = pyqtSignal()

    def __init__(self, x, y, *args, **kwargs):
        """
        Конструктор клекти игровго поля
        """
        super().__init__(*args, **kwargs)
        self.setFixedSize(20, 20)

        self.x = x
        self.y = y

    def reset(self):
        """
        Сброс клетки
        """
        self.is_start = False
        self.is_mine = False
        self.mines_around = 0
        self.is_revealed = False
        self.is_flagged = 0
        self.is_end = False
        self.update()

    def paintEvent(self, event):
        """
        Событие перерисовки клетки
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = event.rect()
        if self.is_revealed:
            color = self.palette().color(QPalette.Background)
            outer, inner = color, color
            if self.is_end:
                inner = Qt.black
        else:
            outer, inner = Qt.gray, Qt.lightGray
        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

        if self.is_revealed:
            if self.is_mine:
                p.drawPixmap(r, QPixmap(IMG_BOMB))
            elif self.is_start:
                p.drawPixmap(r, QPixmap(IMG_START))
            elif self.mines_around > 0:
                pen = QPen(Qt.black)
                p.setPen(pen)
                f = p.font()
                f.setBold(True)
                p.setFont(f)
                p.drawText(r, Qt.AlignCenter, str(self.mines_around))
        elif self.is_flagged:
            p.drawPixmap(r, QPixmap(IMG_FLAG))

    def click(self):
        """
        Обработка клика по клетке
        """
        if not self.is_revealed and not self.is_flagged:
            self.reveal()

    def reveal(self):
        """
        Открытие клетки
        """
        if not self.is_revealed:
            self.reveal_self()
            if self.mines_around == 0:
                self.expandable.emit(self.x, self.y)
            if self.is_mine:
                self.is_end = True
                self.game_over.emit()

    def reveal_self(self):
        """
        Открыть только эту клетку
        """
        self.is_revealed = True
        self.update()

    def toggle_flag(self):
        """
        Сменить статус флага
        """
        self.is_flagged = not self.is_flagged
        self.update()
        self.flagged.emit(self.is_flagged)

    def mouseReleaseEvent(self, event):
        """
        Обработчик нажатия кнопоу мыши
        """
        self.clicked.emit()
        if event.button() == Qt.LeftButton:
            self.click()
        elif event.button() == Qt.RightButton:
            if not self.is_revealed:
                self.toggle_flag()
            else:
                self.accorded.emit(self.x, self.y)
        self.clicked.emit()
                

class MainWindow(QMainWindow):
    """
    Главное окно программы
    """

    def __init__(self, *args, **kwargs):
        """
        Конструктор главного окна
        """
        super().__init__(*args, **kwargs)

        self.level = 0
        self.board_size, self.n_mines = LEVELS[self.level]

        self.setWindowTitle('Сапер')
        self.initUI()
        self.init_map()
        self.update_status(STATUS_READY)
        self._timer = QTimer()
        self._timer.timeout.connect(self.update_timer)
        self._timer.start(1000)
        self.reset_map()

        self.setFixedSize(self.sizeHint())
        self.show()

    def initUI(self):
        """
        Настройка пользовательского интерфейса
        """
        w = QWidget()
        hb = QHBoxLayout()

        self.mines = QLabel(str(self.n_mines))
        self.mines.setAlignment(Qt.AlignCenter)

        self.clock = QLabel('000')
        self.clock.setAlignment(Qt.AlignCenter)

        f = self.mines.font()
        f.setPointSize(24)
        f.setWeight(75)
        self.mines.setFont(f)
        self.clock.setFont(f)

        self.button = QPushButton()
        self.button.setFixedSize(32, 32)
        self.button.setIconSize(QSize(32, 32))
        self.button.setIcon(QIcon('./images/smiley.png'))
        self.button.setFlat(True)
        self.button.pressed.connect(self.button_pressed)

        l = QLabel()
        l.setPixmap(QPixmap.fromImage(IMG_BOMB))
        l.setAlignment(Qt.AlignCenter)
        hb.addWidget(l)

        hb.addWidget(self.mines)
        hb.addWidget(self.button)
        hb.addWidget(self.clock)

        l = QLabel()
        l.setPixmap(QPixmap.fromImage(IMG_CLOCK))
        l.setAlignment(Qt.AlignCenter)
        hb.addWidget(l)

        vb = QVBoxLayout()
        vb.addLayout(hb)

        self.grid = QGridLayout()
        self.grid.setSpacing(5)
        vb.addLayout(self.grid)

        w.setLayout(vb)
        self.setCentralWidget(w)

    def init_map(self):
        """
        Инициализация игрового поля
        """
        for x in range(self.board_size):
            for y in range(self.board_size):
                w = Cell(x, y)
                self.grid.addWidget(w, x, y)
                w.expandable.connect(self.expand_reveal)
                w.clicked.connect(self.handle_click)
                w.game_over.connect(self.game_over)
                w.flagged.connect(self.handle_flag)
                w.accorded.connect(self.handle_accord)

    def reset_map(self):
        self.n_mines = LEVELS[self.level][1]
        self.mines.setText(f'{self.n_mines:03d}')
        self.clock.setText('000')

        for _, _, cell in self.get_all_cells():
            cell.reset()

        self.set_mines()
        self.calc_mines()
        self.set_start()

    def get_all_cells(self):
        """
        Возвращает все клетки
        """
        for x in range(self.board_size):
            for y in range(self.board_size):
                yield (x, y, self.grid.itemAtPosition(x, y).widget())

    def set_mines(self):
        """
        Установка мин на игровое поле
        """
        positions = []
        while len(positions) < self.n_mines:
            x = random.randint(0, self.board_size - 1)
            y = random.randint(0, self.board_size - 1)
            if (x, y) not in positions:
                self.grid.itemAtPosition(x, y).widget().is_mine = True
                positions.append((x, y))
        
    def calc_mines(self):
        """
        Подсчет количества мин
        """
        for x, y, cell in self.get_all_cells():
            cell.mines_around = self.get_mines_around(x, y)

    def get_mines_around(self, x, y):
        """
        Подсчет количества мин вокруг клетки (x, y)
        """
        cells = [cell for _, _, cell in self.get_around_cells(x, y)]
        return sum(1 if cell.is_mine else 0 for cell in cells)

    def get_around_cells(self, x, y):
        """
        Получить список клеток вокруг клетки (x, y)
        """
        positions = []
        for xi in range(max(0, x-1), min(x+2, self.board_size)):
            for yi in range(max(0, y-1), min(y+2, self.board_size)):
                positions.append((xi, yi, self.grid.itemAtPosition(xi, yi).widget()))
        return positions

    def set_start(self):
        """
        Выбор начальной клетки
        """
        empty_cells = [cell
                       for x, y, cell
                       in self.get_all_cells()
                       if cell.mines_around == 0 and not cell.is_mine
                      ]
        start_cell = empty_cells[random.randint(0, len(empty_cells)-1)]
        start_cell.is_start = True

        for _, _, cell in self.get_around_cells(start_cell.x, start_cell.y):
            if not cell.is_mine:
                cell.click()
    
    def expand_reveal(self, x, y):
        """
        Раскрытие пустых клеток
        """
        for _, _, cell in self.get_revealable_cells(x, y):
            cell.reveal()
    
    def get_revealable_cells(self, x, y, force=False):
        """
        Получить список клеток что можно раскрыть вокруг (x, y)
        """
        for xi, yi, cell in self.get_around_cells(x, y):
            if ((force or not cell.is_mine) 
                and not cell.is_flagged 
                and not cell.is_revealed):
                yield (xi, yi, cell)
    
    def update_status(self, status):
        """
        Обновить состояние игры
        """
        self.status = status
        self.button.setIcon(QIcon(STATUS_ICONS[self.status]))

    def handle_click(self):
        """
        Обработчик клика для запуска игры
        """
        if self.status == STATUS_READY:
            self.update_status(STATUS_PLAY)
            self._timer_start_nsecs = int(time.time())
        elif self.status == STATUS_PLAY:
            self.check_win()

    def handle_flag(self, flagged):
        """
        Обработчик сигнала flagged
        """
        self.n_mines += -1 if flagged else 1
        self.mines.setText(f'{self.n_mines:03d}')

    def update_timer(self):
        """
        ОБновить таймер на экране
        """
        if self.status == STATUS_PLAY:
            n_secs = int(time.time()) - self._timer_start_nsecs
            self.clock.setText(f'{n_secs:03d}')

    def game_over(self):
        """
        Обработчик сигнала 'Конец игры'
        """
        self.update_status(STATUS_FAILED)
        self.reveal_map()

    def reveal_map(self):
        """
        Открыть всю карту
        """
        for _, _, cell in self.get_all_cells():
            if not (cell.is_flagged and cell.is_mine):
                cell.reveal_self()

    def check_win(self):
        """
        Проверка победы в игре
        """
        if self.n_mines == 0:
            if all(cell.is_revealed or cell.is_flagged 
                   for _, _, cell in self.get_all_cells()):
                self.update_status(STATUS_SUCCESS)
        else:
            unrevealed = []
            for _, _, cell in self.get_all_cells():
                if not cell.is_revealed and not cell.is_flagged:
                    unrevealed += [cell]
                    if not cell.is_mine or len(unrevealed) > self.n_mines:
                        return
            if len(unrevealed) == self.n_mines:
                if all(cell.is_flagged == cell.is_mine or cell in unrevealed
                       for _, _, cell in self.get_all_cells()):
                    for cell in unrevealed:
                        cell.toggle_flag()
                    self.update_status(STATUS_SUCCESS)

    def button_pressed(self):
        """
        Обработчик нажатий кнопки на панели инструментов
        """
        if self.status == STATUS_PLAY:
            self.update_status(STATUS_FAILED)
            self.reveal_map()
        elif self.status in (STATUS_SUCCESS, STATUS_FAILED):
            self.update_status(STATUS_READY)
            self.reset_map()

    def determine_to_safe_reveal(self, x, y, to_reveal):
        """
        Определить, что можно открыть вокруг открытой клетки
        """
        flagged_count = sum(1 if cell.is_flagged else 0 
                            for _, _, cell in self.get_around_cells(x, y))
        cell = self.grid.itemAtPosition(x, y).widget()
        if flagged_count == cell.mines_around:
            for xi, yi, cell in self.get_revealable_cells(x, y, True):
                if (xi, yi) not in to_reveal:
                    to_reveal += [(xi, yi)]
                    self.determine_to_safe_reveal(xi, yi, to_reveal)

    def handle_accord(self, x, y):
        """
        Обработчик сигнала accorded
        """
        to_reveal = []
        self.determine_to_safe_reveal(x, y, to_reveal)
        for xi, yi in to_reveal:
            self.grid.itemAtPosition(xi, yi).widget().reveal()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec()