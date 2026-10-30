from PySide6.QtCore import Qt,Signal
from PySide6.QtGui import QColor,QPainter,QPen,QPixmap,QFont
from PySide6.QtWidgets import QFrame,QLabel,QPushButton,QVBoxLayout,QHBoxLayout,QToolButton,QCheckBox,QMessageBox as QtMessageBox
from manager.i18n import t

class TranslatedLabel(QLabel):
    def __init__(self,text):self.source_text=str(text);super().__init__(t(text))
    def setText(self,text):self.source_text=str(text);super().setText(t(text))
    def retranslate(self):super().setText(t(self.source_text))

class TranslatedButton(QPushButton):
    def __init__(self,text):self.source_text=str(text);super().__init__(t(text))
    def setText(self,text):self.source_text=str(text);super().setText(t(text))
    def retranslate(self):super().setText(t(self.source_text))

class Messages:
    @staticmethod
    def information(parent,title,text):return QtMessageBox.information(parent,t(title),t(text))
    @staticmethod
    def warning(parent,title,text):return QtMessageBox.warning(parent,t(title),t(text))

def label(text,style="",wrap=False):
    w=TranslatedLabel(text);w.setWordWrap(wrap)
    if style:w.setObjectName(style)
    return w

def button(text,slot=None,primary=False):
    w=TranslatedButton(text);w.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:w.setObjectName("primary")
    if slot:w.clicked.connect(slot)
    return w

def panel():
    frame=QFrame();frame.setObjectName("panel")
    layout=QVBoxLayout(frame);layout.setContentsMargins(22,20,22,20);layout.setSpacing(12)
    return frame,layout

def artwork(series="",size=200):
    pm=QPixmap(size,size);pm.fill(Qt.GlobalColor.transparent)
    p=QPainter(pm);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    accent=QColor("#54dfc5" if "zelda" in series.lower() else "#aaa0ff")
    p.setPen(QPen(QColor("#283a42"),1));p.setBrush(QColor("#19282f"));p.drawEllipse(size*.13,size*.13,size*.74,size*.74)
    p.setBrush(QColor("#243a40"));p.setPen(Qt.PenStyle.NoPen);p.drawRoundedRect(size*.32,size*.25,size*.36,size*.5,12,12)
    p.setPen(QPen(accent,3));p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(size*.37,size*.32,size*.26,size*.35,7,7)
    p.drawArc(int(size*.44),int(size*.42),int(size*.20),int(size*.18),-60*16,120*16)
    p.drawArc(int(size*.44),int(size*.37),int(size*.27),int(size*.28),-60*16,120*16)
    p.setPen(QPen(accent,4));p.drawPoint(int(size*.44),int(size*.51));p.end()
    return pm

class TagCard(QFrame):
    selected=Signal(str);favorite=Signal(str,bool);queued=Signal(str,bool)
    def __init__(self,tag,meta,image=None,checked=False):
        super().__init__();self.tag=tag;self.setObjectName("tagCard");self.setMinimumWidth(215);self.setMaximumWidth(380)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout=QVBoxLayout(self);layout.setContentsMargins(16,12,16,16);layout.setSpacing(8)
        top=QHBoxLayout();self.check=QCheckBox();self.check.setToolTip(t("Check for playlist"));self.check.setChecked(checked)
        self.check.toggled.connect(lambda value:self.queued.emit(tag['sha256'],value));top.addWidget(self.check)
        top.addWidget(label(meta['series'],"eyebrow"));top.addStretch()
        fav=QToolButton();fav.setText("★" if tag['favorite'] else "☆");fav.setCheckable(True);fav.setChecked(bool(tag['favorite']))
        fav.setToolTip(t("Remove from favorites" if tag['favorite'] else "Add to favorites"))
        fav.clicked.connect(lambda value:self.favorite.emit(tag['sha256'],value));top.addWidget(fav);layout.addLayout(top)
        art=QLabel();art.setAlignment(Qt.AlignmentFlag.AlignCenter);art.setFixedHeight(145)
        pix=QPixmap(str(image)) if image else artwork(meta['series'])
        art.setPixmap(pix.scaled(160,140,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));layout.addWidget(art)
        name=label(meta['name'],"cardTitle",True);name.setMinimumHeight(42);layout.addWidget(name)
        if meta.get('reward'):layout.addWidget(label('Possible TOTK rewards · '+meta['reward'],'muted',True))
        layout.addWidget(label(f"{tag['size']} bytes · Format verified","muted"))
        self.setToolTip(t("Format and BCC verified. Amiibo authenticity must be tested in the game."))
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:self.selected.emit(self.tag['sha256'])
        super().mouseReleaseEvent(event)
    def mark(self,active):
        self.setProperty("chosen",active);self.style().unpolish(self);self.style().polish(self)

STYLE='''
QWidget { background:#10171d; color:#e8eef2; font-family:"Segoe UI"; font-size:14px; }
QMainWindow { background:#10171d; }
QFrame#sidebar {background:#0b1117;border-right:1px solid #23303a;}
QFrame#sidebar QLabel {background:transparent;}
QLabel#brand {font-size:22px;font-weight:750;letter-spacing:1px;}
QLabel#title {font-size:28px;font-weight:700;}
QLabel#hero {font-size:32px;font-weight:700;}
QLabel#subtitle,QLabel#muted {color:#98a9b7;}
QLabel#eyebrow {font-size:11px;color:#7fbeb7;font-weight:700;letter-spacing:1px;}
QLabel#cardTitle {font-size:17px;font-weight:650;}
QLabel#stat {font-size:25px;font-weight:700;}
QFrame#panel {background:#17222b;border:1px solid #293742;border-radius:16px;}
QFrame#panel QLabel {background:transparent;}
QFrame#tagCard {background:#17222b;border:2px solid #263640;border-radius:15px;}
QFrame#tagCard QLabel {background:transparent;}
QFrame#tagCard:hover {border-color:#477370;}
QFrame#tagCard[chosen="true"] {border-color:#54dfc5;background:#18302f;}
QPushButton {background:#24333e;border:1px solid #364956;border-radius:9px;padding:11px 16px;font-weight:600;}
QPushButton:hover {background:#304654;}
QPushButton:pressed {background:#162b34;}
QPushButton:disabled {background:#18232b;color:#637482;border-color:#24343f;}
QPushButton#primary {background:#54dfc5;color:#08221e;border-color:#54dfc5;}
QPushButton#primary:hover {background:#83efdc;}
QPushButton#primary:disabled {background:#254941;color:#87a49f;border-color:#254941;}
QPushButton#nav {background:transparent;border:0;text-align:left;padding:13px 16px;color:#9eafbd;}
QPushButton#nav:checked {background:#193530;color:#77ead4;}
QPushButton#nav:hover {background:#1a2831;}
QToolButton {background:transparent;color:#edcd7b;border:0;font-size:23px;padding:0 4px;}
QLineEdit,QComboBox {background:#15212a;border:1px solid #334550;border-radius:8px;padding:10px;color:#e8eef2;}
QLineEdit:focus,QComboBox:focus {border-color:#54dfc5;}
QComboBox QAbstractItemView {background:#17252e;selection-background-color:#245248;}
QScrollArea {border:0;background:transparent;} QScrollBar:vertical {background:#10171d;width:9px;}
QScrollBar::handle:vertical {background:#344a58;border-radius:4px;min-height:25px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
QProgressBar {border:0;border-radius:7px;background:#283740;min-height:14px;text-align:center;}
QProgressBar::chunk {background:#54dfc5;border-radius:7px;}
QTextEdit,QTableWidget {background:#121e26;border:1px solid #2a3b47;border-radius:8px;padding:8px;}
QHeaderView::section {background:#1d2d37;color:#a3b4c0;border:0;padding:8px;}
QTableWidget::item {padding:6px;} QTableWidget::item:selected {background:#245248;}
QCheckBox {spacing:8px;} QCheckBox::indicator {width:17px;height:17px;}
QLabel#badge {background:#203830;color:#7be7c7;border-radius:10px;padding:8px 14px;font-size:12px;font-weight:650;}
QLabel#badge[tone="muted"] {background:#25333e;color:#acbac5;}
QLabel#badge[tone="warning"] {background:#4a391e;color:#f2cc82;}
QLabel#badge[tone="error"] {background:#4b2831;color:#ffb1bd;}
QLabel#badge[tone="info"] {background:#203c51;color:#9ed8ff;}
QLabel#testBanner {background:#5a431d;color:#ffe2a4;padding:8px;border-radius:6px;}
QMessageBox {background:#17222b;}
'''
