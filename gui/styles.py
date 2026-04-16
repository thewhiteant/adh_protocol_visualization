QMainWindow {
    background-color: COLOR_BACKGROUND;
    color: COLOR_TEXT;
}

QWidget {
    background-color: COLOR_BACKGROUND;
    color: COLOR_TEXT;
}

QLabel {
    color: COLOR_TEXT;
}

QLineEdit {
    background-color: COLOR_BACKGROUND;
    color: COLOR_TEXT;
    border: 1px solid COLOR_TEXT;
}

QLineEdit:focus {
    border: 2px solid COLOR_TEXT;
}

QPushButton {
    background-color: COLOR_BACKGROUND;
    color: COLOR_TEXT;
    border: 1px solid COLOR_TEXT;
}

QPushButton:hover {
    background-color: COLOR_TEXT;
    color: COLOR_BACKGROUND;
}

QPushButton:pressed {
    background-color: COLOR_TEXT;
    color: COLOR_BACKGROUND;
    padding-left: 2px;
    padding-top: 2px;
}

QTextEdit {
    background-color: COLOR_BACKGROUND;
    color: COLOR_TEXT;
    border: 1px solid COLOR_TEXT;
}

QListWidget {
    background-color: COLOR_BACKGROUND;
    color: COLOR_TEXT;
    border: 1px solid COLOR_TEXT;
}

QGroupBox {
    border: 1px solid COLOR_TEXT;
    margin-top: 12px;
}

QComboBox {
    background-color: COLOR_BACKGROUND;
    color: COLOR_TEXT;
    border: 1px solid COLOR_TEXT;
}

QScrollBar:vertical {
    background: COLOR_BACKGROUND;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: COLOR_TEXT;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
}