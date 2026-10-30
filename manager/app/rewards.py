from PySide6.QtWidgets import QDialog,QVBoxLayout,QLineEdit,QComboBox,QTextBrowser
from manager.core.rewards import searchable
from .widgets import label,button
from manager.i18n import t

class RewardsDialog(QDialog):
    def __init__(self,rewards,identity='',parent=None):
        super().__init__(parent);self.rewards=rewards
        self.setWindowTitle(t('Amiibo rewards · Tears of the Kingdom'));self.resize(830,720);self.setMinimumSize(620,500)
        layout=QVBoxLayout(self);layout.setContentsMargins(24,22,24,22);layout.setSpacing(12)
        layout.addWidget(label('TOTK rewards','title'))
        self.search=QLineEdit();self.search.setPlaceholderText(t('Search: Epona, armor, fabric, Link…'));layout.addWidget(self.search)
        self.combo=QComboBox();layout.addWidget(self.combo)
        self.browser=QTextBrowser();self.browser.setOpenExternalLinks(True);layout.addWidget(self.browser,1)
        layout.addWidget(button('Close',self.accept))
        self.search.textChanged.connect(self.filter);self.combo.currentIndexChanged.connect(self.render)
        self.filter();self.combo.setCurrentIndex(self.combo.findData(rewards.for_id(identity)['key']))
    def filter(self):
        old=self.combo.currentData();self.combo.blockSignals(True);self.combo.clear();query=searchable(self.search.text())
        for p in self.rewards.profiles:
            if not query or query in searchable(self.rewards.text(p)+' '+t(self.rewards.text(p))):self.combo.addItem(t(p['name']),p['key'])
        index=self.combo.findData(old)
        self.combo.setCurrentIndex(index if index>=0 else 0);self.combo.blockSignals(False);self.render()
    def render(self):
        key=self.combo.currentData();self.browser.setHtml(t(self.rewards.html(self.rewards.by_key[key]) if key else '<p>No entries match your search.</p>'))
