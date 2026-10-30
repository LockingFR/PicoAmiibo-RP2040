from pathlib import Path
import sys
import threading
import time
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QUrl
from PySide6.QtGui import QDesktopServices,QIcon
from PySide6.QtWidgets import (QMainWindow,QWidget,QFrame,QVBoxLayout,QHBoxLayout,QGridLayout,
    QStackedWidget,QScrollArea,QFileDialog,QMessageBox,QLineEdit,QComboBox,QCheckBox,
    QProgressBar,QTextEdit,QTableWidget,QTableWidgetItem,QHeaderView,QListWidget)
from manager import __version__
from manager.core.metadata import Metadata
from manager.core.guide import instructions
from manager.core.rewards import Rewards,searchable
from .rewards import RewardsDialog
from manager.transport.discovery import discover
from manager.transport.cdc import Transport,friendly_error
from .widgets import label,button,panel,TagCard,STYLE,artwork,Messages,TranslatedLabel,TranslatedButton
from manager.i18n import t,set_language,language
QMessageBox=Messages

class Task(QThread):
    result=Signal(object);error=Signal(object);progress=Signal(object)
    def __init__(self,fn):super().__init__();self.fn=fn
    def run(self):
        try:self.result.emit(self.fn(self.progress.emit))
        except Exception as error:self.error.emit(error)

class MainWindow(QMainWindow):
    def __init__(self,library,transport=None,no_usb=False,test_mode=False):
        super().__init__();self.library=library;self.transport=transport or Transport();self.no_usb=no_usb
        set_language(library.setting('language','en'))
        self.metadata=Metadata(library.cache);self.rewards=Rewards();self.devices=[];self.device=None;self.probe=None
        self.selected=library.setting('selected','');self._tasks={};self._closing=False
        queued=library.setting('playlist_selection',[])
        self.checked=list(dict.fromkeys(sha for sha in queued if isinstance(sha,str) and library.get(sha))) if isinstance(queued,list) else []
        self._last_probe=0.;self._probe_key='';self._cancel=threading.Event();self._cards=[]
        self._last_version='';self._guide_step=0;self._last_record=None;self._guide_blocked=False;self._error_message=''
        self.setWindowTitle(f'PicoAmiibo Manager · {__version__}');self.setMinimumSize(950,700)
        self.resize(*library.setting('window_size',[1220,820]));self.setStyleSheet(STYLE)
        self.setWindowIcon(QIcon(artwork('Zelda',128)))
        root=QWidget();self.setCentralWidget(root);outer=QHBoxLayout(root);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        side=QFrame();side.setObjectName('sidebar');side.setFixedWidth(210);outer.addWidget(side)
        nav=QVBoxLayout(side);nav.setContentsMargins(18,28,18,22);nav.setSpacing(8)
        nav.addWidget(label('PICO AMIIBO','brand'));nav.addWidget(label('MANAGER  /  '+__version__,'eyebrow',True));nav.addSpacing(34)
        self.nav=[]
        for i,text in enumerate(('⌂   Home','▦   Library','↑   Load','↗   Switch 2','⚙   Diagnostics')):
            b=button(text,lambda checked=False,index=i:self.page(index));b.setObjectName('nav');b.setCheckable(True);nav.addWidget(b);self.nav.append(b)
        nav.addStretch();self.side_status=label('Looking for your Pico…','muted',True);nav.addWidget(self.side_status)
        nav.addSpacing(16);nav.addWidget(label('Local USB · one active tag\nNo account required','muted',True))
        body=QVBoxLayout();body.setContentsMargins(30,28,30,22);body.setSpacing(22);outer.addLayout(body,1)
        header=QHBoxLayout();titles=QVBoxLayout();self.heading=label('Home','title');titles.addWidget(self.heading)
        self.subtitle=label('Your library, your Pico, your next adventure.','subtitle',True);titles.addWidget(self.subtitle)
        header.addLayout(titles,1);self.badge=label('Pico not detected','badge');self.badge.setMaximumHeight(40);header.addWidget(self.badge);body.addLayout(header)
        if test_mode:
            body.addWidget(label('TEST · Isolated profile, artificial data, USB access disabled','testBanner'))
        else:body.addWidget(label('PREVIEW · New multi-slot firmware requires a separate physical test.','testBanner',True))
        self.pages=QStackedWidget();body.addWidget(self.pages,1)
        self._home();self._library();self._transfer();self._guide();self._diagnostics()
        self.page(0);self.refresh_library();self.refresh_history();self._update_device_ui()
        self.timer=QTimer(self);self.timer.timeout.connect(self.scan);self.timer.start(2000)
        if not no_usb:QTimer.singleShot(100,self.scan)

    def _shell_page(self):
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame)
        w=QWidget();lay=QVBoxLayout(w);lay.setContentsMargins(0,0,8,0);lay.setSpacing(18);lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(w);self.pages.addWidget(scroll);return lay
    def page(self,index):
        self.pages.setCurrentIndex(index)
        names=('Home','Library','Load onto the Pico','Switch 2 guide','Diagnostics and settings')
        self.heading.setText(names[index])
        for i,b in enumerate(self.nav):b.setChecked(i==index)
        if index==3:self._render_guide()
        if index==4:self.refresh_history()
    def _home(self):
        lay=self._shell_page();hero,hl=panel();hl.addWidget(label('YOUR LIBRARY, READY TO GO','eyebrow'))
        hl.addWidget(label('One amiibo. One click.','hero'));hl.addWidget(label('Load your Pico here. Continue on your Switch 2.','subtitle',True))
        actions=QHBoxLayout();actions.addWidget(button('Choose an amiibo',lambda:self.page(1),True))
        actions.addWidget(button('Import files',self.import_files));actions.addStretch();hl.addLayout(actions);lay.addWidget(hero)
        card,cl=panel();cl.addWidget(label('Your Pico','cardTitle'));self.home_device=label('Pico disconnected','stat');cl.addWidget(self.home_device)
        self.home_hint=label('Connect your Pico to the PC with a USB data cable.','muted',True);cl.addWidget(self.home_hint)
        row=QHBoxLayout();row.addWidget(button('How to connect your Pico',self.connection_help));row.addWidget(button('Diagnostics',lambda:self.page(4)));row.addStretch();cl.addLayout(row);lay.addWidget(card)
        row=QHBoxLayout();self.home_stats=[]
        for title in ('In your library','Amiibo on the Pico','Last verification'):
            p,l=panel();l.addWidget(label(title,'muted'));value=label('—','cardTitle',True);l.addWidget(value);self.home_stats.append(value);row.addWidget(p,1)
        lay.addLayout(row)
        p,l=panel();l.addWidget(label('From PC to Switch 2','cardTitle'))
        l.addWidget(label('After a verified readback, the guide helps you connect the Pico to your console. You must confirm the result in the game.','muted',True))
        l.addWidget(button('Open the Switch 2 guide',lambda:self.page(3)));lay.addWidget(p)
    def _library(self):
        lay=self._shell_page();row=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText(t('Search amiibo or rewards…'));self.search.textChanged.connect(self.render_cards);row.addWidget(self.search,1)
        self.series=QComboBox();self.series.addItem('All series');self.series.currentTextChanged.connect(self.render_cards);row.addWidget(self.series)
        self.favorites=QCheckBox(t('Favorites'));self.favorites.toggled.connect(self.render_cards);row.addWidget(self.favorites)
        row.addWidget(button('＋ Import',self.import_files,True));lay.addLayout(row)
        self.library_info=label('No amiibo imported','muted',True);lay.addWidget(self.library_info)
        row=QHBoxLayout();row.addWidget(button('Select all shown',self.check_shown));row.addWidget(button('Clear checked',self.clear_checked))
        self.checked_count=label('0 checked tags','muted');row.addWidget(self.checked_count);row.addStretch();lay.addLayout(row)
        self.grid_widget=QWidget();self.grid=QGridLayout(self.grid_widget);self.grid.setContentsMargins(0,0,0,0);self.grid.setSpacing(16);lay.addWidget(self.grid_widget)
        self.empty_library=label('Your library starts here.\nImport your 540-byte or 572-byte .bin files. Unidentified files remain usable.','muted',True);lay.addWidget(self.empty_library)
        row=QHBoxLayout();self.library_load=button('Load selection',lambda:self.page(2),True);row.addWidget(self.library_load)
        self.rewards_selected=button('Selected amiibo rewards',self.show_selected_rewards);row.addWidget(self.rewards_selected);row.addStretch();lay.addLayout(row)
        self.rewards_explore=button('Explore all TOTK rewards',self.show_rewards);lay.addWidget(self.rewards_explore)
        self.batch_button=button('Load checked tags',self.open_playlist,True);lay.addWidget(self.batch_button)
    def _transfer(self):
        lay=self._shell_page();card,cl=panel();cl.addWidget(label('1 · Choose your Pico and amiibo','cardTitle'))
        self.port_combo=QComboBox();self.port_combo.setPlaceholderText(t('No Pico in configuration mode'));self.port_combo.currentIndexChanged.connect(self.port_changed);cl.addWidget(self.port_combo)
        cl.addWidget(label('Choose what to load','muted'))
        self.mode_combo=QComboBox();self.mode_combo.addItem(t('Single amiibo (replace playlist)'),'single')
        self.mode_combo.addItem(t('Checked amiibo playlist'),'playlist');self.mode_combo.currentIndexChanged.connect(self.transfer_mode_changed);cl.addWidget(self.mode_combo)
        self.tag_combo=QComboBox();self.tag_combo.setPlaceholderText(t('Import an amiibo into your library'));self.tag_combo.currentIndexChanged.connect(self.tag_changed);cl.addWidget(self.tag_combo)
        self.playlist_items=QListWidget();self.playlist_items.setMinimumHeight(100);self.playlist_items.setMaximumHeight(210);cl.addWidget(self.playlist_items)
        self.playlist_hint=label('Select up to 64 amiibo.','muted',True);cl.addWidget(self.playlist_hint)
        self.transfer_hint=label('Hold BOOTSEL for two seconds to enter configuration mode.','muted',True);cl.addWidget(self.transfer_hint)
        self.load_button=button('Load and verify',self.start_upload,True);self.load_button.setObjectName('primary');cl.addWidget(self.load_button);lay.addWidget(card)
        card,cl=panel();cl.addWidget(label('2 · Save and read back','cardTitle'))
        self.phase_label=label('Waiting to load','cardTitle',True);cl.addWidget(self.phase_label)
        self.progress=QProgressBar();self.progress.setRange(0,100);self.progress.setValue(0);self.progress.setTextVisible(False);cl.addWidget(self.progress)
        self.progress_bytes=label('Progress measures the bytes actually transmitted and read back.','muted',True);cl.addWidget(self.progress_bytes)
        self.transfer_result=label('A verified transfer does not confirm recognition in the game.','muted',True);cl.addWidget(self.transfer_result)
        row=QHBoxLayout();self.cancel_button=button('Cancel operation',self.cancel_upload);self.cancel_button.setEnabled(False);row.addWidget(self.cancel_button)
        self.guide_button=button('Continue to Switch 2',lambda:self.page(3));self.guide_button.setEnabled(False);row.addWidget(self.guide_button);cl.addLayout(row);lay.addWidget(card)
    def _guide(self):
        lay=self._shell_page();card,cl=panel();self.guide_version=label('Guide version: unknown','eyebrow');cl.addWidget(self.guide_version)
        self.guide_number=label('Before you start','muted');cl.addWidget(self.guide_number)
        self.guide_text=label('Load an amiibo and verify its readback before connecting to the console.','hero',True);cl.addWidget(self.guide_text)
        row=QHBoxLayout();self.guide_prev=button('Previous',lambda:self.guide_move(-1));row.addWidget(self.guide_prev)
        self.guide_next=button('Next step',lambda:self.guide_move(1),True);row.addWidget(self.guide_next);row.addStretch();cl.addLayout(row);lay.addWidget(card)
        p,l=panel();l.addWidget(label('What did you observe in the game?','cardTitle'))
        l.addWidget(label('This confirmation is saved as your observation. The PC cannot read the Pico while it is connected to the console.','muted',True))
        row=QHBoxLayout();self.game_ok=button('The amiibo was recognized',lambda:self.game_feedback('recognized'),True);row.addWidget(self.game_ok)
        self.game_fail=button('The scan failed',lambda:self.game_feedback('failed'));row.addWidget(self.game_fail);l.addLayout(row)
        self.game_status=label('No game result reported.','muted',True);l.addWidget(self.game_status);lay.addWidget(p)
        p,l=panel();l.addWidget(label('If scanning fails','cardTitle'));l.addWidget(label('Open the amiibo scan in your game, present and remove the tag using the gestures for your firmware version, and use a USB data cable. Return to the PC to read the stored data if needed. A successful readback does not establish cryptographic authenticity.','muted',True));lay.addWidget(p)
    def _diagnostics(self):
        lay=self._shell_page();p,l=panel();l.addWidget(label('Connection and protocol','cardTitle'))
        self.diag_text=label('No device detected.','muted',True);l.addWidget(self.diag_text)
        row=QHBoxLayout();self.probe_button=button('Test communication',self.probe_device);row.addWidget(self.probe_button);row.addWidget(button('Find the Pico',self.scan));row.addWidget(button('Export log',self.export_log));l.addLayout(row);lay.addWidget(p)
        p,l=panel();l.addWidget(label('Preferences and local data','cardTitle'))
        row=QHBoxLayout();row.addWidget(label('Language'));self.language_combo=QComboBox()
        self.language_combo.addItem('English','en');self.language_combo.addItem('Français','fr')
        self.language_combo.setCurrentIndex(self.language_combo.findData(language()));self.language_combo.currentIndexChanged.connect(self.change_language)
        row.addWidget(self.language_combo,1);l.addLayout(row)
        self.totk_rewards=QCheckBox(t('Show TOTK rewards'));self.totk_rewards.setChecked(self.library.setting('show_totk_rewards',True));self.totk_rewards.toggled.connect(self.set_totk_rewards);l.addWidget(self.totk_rewards)
        self.online=QCheckBox(t('Enable online metadata and artwork (optional)'));self.online.setChecked(self.library.setting('online_metadata',False));self.online.toggled.connect(self.set_online);l.addWidget(self.online)
        l.addWidget(label('Only a public catalog and public images are downloaded. Amiibo files are never uploaded. Cached images remain available offline.','muted',True))
        self.metadata_button=button('Refresh metadata',self.refresh_metadata);self.metadata_button.setEnabled(self.online.isChecked());l.addWidget(self.metadata_button)
        l.addWidget(button('Open data folder',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.library.root)))));lay.addWidget(p)
        p,l=panel();l.addWidget(label('Load history','cardTitle'))
        self.history_table=QTableWidget(0,5);self.history_table.setHorizontalHeaderLabels([t(x) for x in ['Date','Amiibo','Port','Verification','Game']])
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.history_table.horizontalHeader().setStretchLastSection(True);self.history_table.setMinimumHeight(230);l.addWidget(self.history_table);lay.addWidget(p)
        p,l=panel();l.addWidget(label('Recovery and versions','cardTitle'));l.addWidget(label(f'Manager {__version__} · Windows x64\nThe Manager never flashes firmware. Recovery: hold BOOTSEL while connecting the Pico to the PC, confirm the correct RPI-RP2 drive, then manually copy the recovery UF2.\n0.1.1: release preceding the reported Epona success. 0.1.2: version without L+R; separate console qualification.','muted',True));lay.addWidget(p)
        l.addWidget(button('Open recovery firmware folder',self.open_firmwares))
        l.addWidget(label('0.2.0 preview: checked playlists and five-second cycling; physical qualification pending.','muted',True))

    def _start(self,key,fn,done,error=None):
        if key in self._tasks:return
        task=Task(fn);self._tasks[key]=task
        task.result.connect(done);task.error.connect(error or self._job_error)
        if key=='upload':task.progress.connect(self.upload_progress)
        def finish():
            self._tasks.pop(key,None);task.deleteLater();self._update_device_ui()
            if self._closing and not self._tasks:QTimer.singleShot(0,self.close)
        task.finished.connect(finish);task.start();self._update_buttons()
    def _job_error(self,error):
        self._error_message=friendly_error(error);self._update_device_ui()
    def io_busy(self):return 'probe' in self._tasks or 'upload' in self._tasks
    def scan(self):
        if self.no_usb or self.io_busy() or self._closing:return
        self._start('scan',lambda _:discover(),self.scanned)
    def scanned(self,devices):
        self.devices=devices;cdc=[d for d in devices if d.kind=='cdc']
        old=self.port_combo.currentData();self.port_combo.blockSignals(True);self.port_combo.clear()
        if len(cdc)>1:self.port_combo.addItem(t('Select the correct Pico explicitly'),None)
        for d in cdc:self.port_combo.addItem(t(f'{d.port} · PicoAmiibo Config · {d.version or "unknown version"}'),d.port)
        if old:
            index=self.port_combo.findData(old)
            if index>=0:self.port_combo.setCurrentIndex(index)
        if len(cdc)==1:self.port_combo.setCurrentIndex(0)
        self.port_combo.blockSignals(False)
        chosen=self.port_combo.currentData();self.device=next((d for d in cdc if d.port==chosen),None)
        if not self.device:self.probe=None;self._probe_key=''
        self._update_device_ui()
        if self.device:
            key=self.device.port+'|'+self.device.serial
            if key!=self._probe_key or time.monotonic()-self._last_probe>10:self.probe_device()
    def port_changed(self):
        chosen=self.port_combo.currentData();self.device=next((d for d in self.devices if d.port==chosen and d.kind=='cdc'),None)
        self.probe=None;self._update_device_ui()
        if self.device:self.probe_device()
    def probe_device(self):
        if not self.device or self.io_busy():return
        device=self.device;self._probe_key=device.port+'|'+device.serial;self._last_probe=time.monotonic()
        def done(result):
            if self.device and self.device.port==device.port:
                self.probe=result;self._error_message='';self._last_version=device.version;self._update_device_ui()
        def failed(error):self.probe=None;self._job_error(error)
        self._start('probe',lambda _:self.transport.probe(device.port),done,failed)
    def _update_device_ui(self):
        if self.device:
            title='USB configuration';hint='The Pico is ready to receive an amiibo.' if self.probe else 'Checking communication…'
            if self.probe:title='Pico identified · '+self.device.port
        elif any(d.kind=='bootloader' for d in self.devices):title='BOOTSEL / RPI-RP2 mode';hint='The Pico is in its bootloader. Manually install your firmware, then restart it to load an amiibo.'
        elif len([d for d in self.devices if d.kind=='cdc'])>1:title='Multiple Pico devices detected';hint='Choose the correct Pico port on the Load page.'
        elif any(d.kind=='controller_candidate' for d in self.devices):title='Controller mode · unidentified';hint='In controller mode, release BOOTSEL after 2 seconds and before 5 seconds to open configuration.'
        else:title='Pico not detected';hint='Connect your Pico to the PC using a USB data cable, then hold BOOTSEL for two seconds after startup.'
        if self._error_message:hint=self._error_message
        elif self.is_playlist() and len(self.checked)>1 and self.probe and not self.probe.get('supports_playlist'):
            hint='Multi-slot firmware 0.2.0 is required for multiple tags.'
        self.badge.setText('Transfer in progress' if 'upload' in self._tasks else title);self.home_device.setText(title)
        tone='error' if self._error_message else 'info' if 'upload' in self._tasks else 'ok' if self.probe else 'warning' if self.devices else 'muted'
        self.badge.setProperty('tone',tone);self.badge.style().unpolish(self.badge);self.badge.style().polish(self.badge)
        self.home_hint.setText(hint);self.transfer_hint.setText(hint);self.side_status.setText(title)
        current='Unidentified'
        if self.probe:
            if not self.probe['loaded']:current='No stored tag'
            elif self.probe.get('sha256'):
                tag=self.library.get(self.probe['sha256']) or {'name':'Unidentified amiibo','amiibo_id':self.probe.get('amiibo_id','')}
                current=self.metadata.get(tag)['name']
        self.home_stats[1].setText(current)
        details=[f'Mode: {title}',f'Application: {__version__}']
        if self.device:details += [f'Port: {self.device.port}',f'Version from USB serial: {self.device.version or "unknown"}',f'USB identity: {self.device.serial or "unavailable"}']
        if self.probe:details += [f'PA1 protocol: confirmed',f'Tag loaded: {bool(self.probe["loaded"])}',f'Size: {self.probe["size"]} bytes · CRC : {self.probe["crc"]}',f'Generation: {self.probe["generation"]} · Presented: {bool(self.probe["presented"])}']
        if self.probe and self.probe.get('supports_playlist') and self.probe['slot_count']:
            details.append(f'{self.probe["slot_count"]} stored tags · active #{self.probe["slot_index"]+1}')
        if self._error_message:details.append(self._error_message)
        self.diag_text.setText('\n'.join(details));self._update_buttons()
    def _update_buttons(self):
        if not hasattr(self,'load_button'):return
        count=len(self.checked)
        selection_ok=bool(self.selected) if not self.is_playlist() else 0<count<=64
        capability_ok=not self.is_playlist() or count==1 or bool(self.probe and self.probe.get('supports_playlist') and count<=self.probe.get('max_slots',0))
        self.load_button.setEnabled(bool(self.device and selection_ok and capability_ok and not self.io_busy()))
        self.probe_button.setEnabled(bool(self.device and not self.io_busy()))
        self.cancel_button.setEnabled('upload' in self._tasks)
        self.port_combo.setEnabled(not self.io_busy());self.tag_combo.setEnabled(not self.io_busy() and not self.is_playlist())
        self.mode_combo.setEnabled(not self.io_busy());self.batch_button.setEnabled(0<count<=64 and not self.io_busy())
        self.library_load.setEnabled(bool(self.selected));self.rewards_selected.setEnabled(bool(self.selected));self.metadata_button.setEnabled(self.online.isChecked() and 'metadata' not in self._tasks)
    def connection_help(self):
        QMessageBox.information(self,'Connect your Pico','1. Connect the Pico to the PC using a USB data cable.\n2. After startup, hold BOOTSEL for 2 seconds and release.\n3. The LED flashes quickly and the configuration port appears.\n\nHolding BOOTSEL before connecting opens RPI-RP2 for firmware recovery. It is not the amiibo import channel.')
    def import_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,t('Import your amiibo'),'',t('Amiibo files (*.bin)'))
        if paths:self.import_paths(paths)
    def import_paths(self,paths):
        added=duplicates=0;errors=[]
        for path in paths:
            try:
                item,created=self.library.import_file(path);added+=int(created);duplicates+=int(not created)
                self.selected=item['sha256'];self.library.set_setting('selected',self.selected)
            except (OSError,ValueError):errors.append(Path(path).name)
        self.refresh_library();self.page(1)
        self.library_info.setText(f'{added} imported · {duplicates} duplicates skipped'+(f' · {len(errors)} files rejected' if errors else ''))
        if errors:QMessageBox.warning(self,'Files rejected','Invalid size or structure, or inaccessible file:\n'+'\n'.join(errors[:12]))
    def refresh_library(self):
        self.tags=self.library.all();self.home_stats[0].setText(str(len(self.tags))+' amiibo')
        if self.selected and not self.library.get(self.selected):self.selected=''
        self.tag_combo.blockSignals(True);self.tag_combo.clear()
        for tag in self.tags:self.tag_combo.addItem(t(self.metadata.get(tag)['name']),tag['sha256'])
        if self.selected:self.tag_combo.setCurrentIndex(self.tag_combo.findData(self.selected))
        elif self.tags:self.selected=self.tags[0]['sha256'];self.tag_combo.setCurrentIndex(0)
        self.tag_combo.blockSignals(False)
        current=self.series.currentText();self.series.blockSignals(True);self.series.clear();self.series.addItem(t('All series'))
        self.series.addItems(sorted({t(self.metadata.get(item)['series']) for item in self.tags}));index=self.series.findText(current)
        if index>=0:self.series.setCurrentIndex(index)
        self.series.blockSignals(False);self.render_cards();self._update_playlist_ui();self._update_buttons()
    def render_cards(self):
        if not hasattr(self,'tags'):return
        show_totk=self.totk_rewards.isChecked()
        self.rewards_selected.setVisible(show_totk);self.rewards_explore.setVisible(show_totk)
        self.search.setPlaceholderText(t('Search amiibo or rewards…' if show_totk else 'Search amiibo or characters…'))
        while self.grid.count():
            item=self.grid.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self._cards=[];query=searchable(self.search.text());series=self.series.currentText();shown=[]
        for tag in self.tags:
            meta=self.metadata.get(tag)
            reward_text=''
            if show_totk:
                profile=self.rewards.for_id(tag['amiibo_id']);meta['reward']=profile['highlight'];reward_text=self.rewards.text(profile)
            haystack=' '.join([tag['name'],meta['name'],meta['character'],meta['series'],reward_text])
            if query and query not in searchable(haystack+' '+t(haystack)):continue
            if self.series.currentIndex()>0 and t(meta['series'])!=series:continue
            if self.favorites.isChecked() and not tag['favorite']:continue
            shown.append((tag,meta))
        columns=max(1,min(3,(self.width()-290)//245))
        for i,(tag,meta) in enumerate(shown):
            card=TagCard(tag,meta,self.metadata.image_path(tag),tag['sha256'] in self.checked);card.selected.connect(self.open_tag)
            card.queued.connect(self.queue_tag);card.favorite.connect(self.favorite_tag);card.mark(tag['sha256']==self.selected)
            self.grid.addWidget(card,i//columns,i%columns);self._cards.append(card)
        self.empty_library.setVisible(not shown);self.library_info.setText(f'{len(shown)} shown · {len(self.tags)} in your library')
    def select_tag(self,sha):
        self.selected=sha;self.library.set_setting('selected',sha)
        for card in self._cards:card.mark(card.tag['sha256']==sha)
        self.tag_combo.blockSignals(True);self.tag_combo.setCurrentIndex(self.tag_combo.findData(sha));self.tag_combo.blockSignals(False);self._update_buttons()
    def tag_changed(self):
        if self.tag_combo.currentData():self.select_tag(self.tag_combo.currentData())
    def open_tag(self,sha):
        self.select_tag(sha);self.mode_combo.setCurrentIndex(0);self.page(2)
    def is_playlist(self):return hasattr(self,'mode_combo') and self.mode_combo.currentData()=='playlist'
    def queue_tag(self,sha,checked):
        if checked and sha not in self.checked:self.checked.append(sha)
        elif not checked and sha in self.checked:self.checked.remove(sha)
        self.library.set_setting('playlist_selection',self.checked);self._update_playlist_ui();self._update_device_ui()
    def check_shown(self):
        for card in self._cards:
            if card.tag['sha256'] not in self.checked:self.checked.append(card.tag['sha256'])
            card.check.blockSignals(True);card.check.setChecked(True);card.check.blockSignals(False)
        self.library.set_setting('playlist_selection',self.checked);self._update_playlist_ui();self._update_device_ui()
    def clear_checked(self):
        self.checked=[];self.library.set_setting('playlist_selection',[])
        for card in self._cards:
            card.check.blockSignals(True);card.check.setChecked(False);card.check.blockSignals(False)
        self._update_playlist_ui();self._update_device_ui()
    def open_playlist(self):
        self.mode_combo.setCurrentIndex(1);self.page(2)
    def transfer_mode_changed(self):
        if hasattr(self,'playlist_items'):self._update_playlist_ui();self._update_device_ui()
    def _update_playlist_ui(self):
        if not hasattr(self,'checked_count'):return
        self.checked=[sha for sha in self.checked if self.library.get(sha)]
        self.checked_count.setText(f'{len(self.checked)} checked tags')
        self.playlist_items.clear()
        for index,sha in enumerate(self.checked):
            tag=self.library.get(sha);self.playlist_items.addItem(f'{index+1}. '+t(self.metadata.get(tag)['name']))
        batch=self.is_playlist();self.playlist_items.setVisible(batch);self.playlist_hint.setVisible(batch)
        self.tag_combo.setVisible(not batch)
        hint='Maximum 64 tags; reduce the checked selection.' if len(self.checked)>64 else 'Select up to 64 amiibo.'
        if len(self.checked)>1:hint+=' '+('One active tag at a time. Hold 5 seconds to advance; short tap to present.')
        self.playlist_hint.setText(hint)
        self.load_button.setText('Load checked playlist' if batch else 'Load and verify')
        self._update_buttons()
    def favorite_tag(self,sha,value):self.library.favorite(sha,value);self.refresh_library()
    def show_selected_rewards(self):
        tag=self.library.get(self.selected)
        if tag:self.show_rewards(tag['amiibo_id'])
    def show_rewards(self,identity=''):
        RewardsDialog(self.rewards,identity if isinstance(identity,str) else '',self).exec()
    def start_upload(self):
        if not self.device or self.io_busy():return
        identities=self.checked[:] if self.is_playlist() else ([self.selected] if self.selected else [])
        if not identities or len(identities)>64:return
        if len(identities)>1 and not (self.probe and self.probe.get('supports_playlist')):
            QMessageBox.information(self,'Firmware capability','Multi-slot firmware 0.2.0 is required for multiple tags.');return
        try:images=[self.library.data(sha) for sha in identities];data=images[0]
        except (ValueError,OSError) as error:QMessageBox.warning(self,'Local file',str(error));return
        tag=self.library.get(identities[0]);device=self.device;self._cancel=threading.Event();self.guide_button.setEnabled(False)
        name=self.metadata.get(tag)['name'] if len(images)==1 else f'Playlist ({len(images)})'
        total_size=sum(map(len,images))
        self._last_record=None;self._guide_blocked=True
        self.transfer_result.setText('Keep the Pico connected during this operation.');self._last_version=device.version
        def done(result):
            self._error_message=''
            self.probe=result;self.phase_label.setText('Saved and verified on the Pico');self.progress.setRange(0,100);self.progress.setValue(100)
            text='Identical readback · '+str(len(data))+' bytes · CRC '+result['crc']
            if len(images)>1:
                self.phase_label.setText('Playlist saved and verified')
                text=f'{len(images)} tags verified; first tag active, ejected.'
            if not result['exit_ok']:text+='\nReturning to controller mode was not confirmed. Disconnect and reconnect the Pico to restart it.'
            self.transfer_result.setText(text);self.guide_button.setEnabled(True)
            self._last_record=self.library.record(name,device.port,device.version,total_size,result['crc'],'verified',text)
            self._guide_blocked=False
            self._guide_step=0;self.refresh_history();self._update_device_ui()
        def failed(error):
            message=friendly_error(error);self.probe=None;self.phase_label.setText('Load not verified');self.progress.setRange(0,100);self.progress.setValue(0)
            self.transfer_result.setText(message);self.library.record(name,device.port,device.version,total_size,tag['crc'] if len(images)==1 else '','failed',message);self.refresh_history();self._error_message=message;self._update_device_ui()
        self.page(2)
        def transfer(emit):
            progress=lambda *x:emit(x)
            if len(images)>1:return self.transport.upload_playlist(device.port,images,progress,self._cancel)
            return self.transport.upload(device.port,data,progress,self._cancel)
        self._start('upload',transfer,done,failed)
    def upload_progress(self,event):
        stage,done,total=event
        self.badge.setText('Transfer in progress');self.badge.setProperty('tone','info');self.badge.style().unpolish(self.badge);self.badge.style().polish(self.badge)
        names={'identify':'Identifying the Pico','capability':'Checking playlist capability','write':'Sending to the Pico','commit':'Saving to flash…','committed':'Save confirmed','readback':'Reading back from the Pico','compare':'Comparing data','verified':'Readback compared and verified'}
        self.phase_label.setText(names.get(stage,stage))
        if total:self.progress.setRange(0,total);self.progress.setValue(done);self.progress_bytes.setText(f'{done} / {total} bytes'+(' read back' if stage=='readback' else ' sent' if stage=='write' else ' verified'))
        else:self.progress.setRange(0,0);self.progress_bytes.setText('Waiting for a response from the Pico…')
    def cancel_upload(self):self._cancel.set();self.cancel_button.setEnabled(False);self.transfer_result.setText('Cancellation requested. Read the Pico again if verification does not finish.')
    def refresh_history(self):
        rows=self.library.history();self.history_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            values=(r['date'].replace('T',' ')[:19],r['name'],r['port'],'Verified readback' if r['status']=='verified' else 'Not verified',{'recognized':'Recognized · reported','failed':'Failed · reported'}.get(r['game_result'],'Not confirmed'))
            for j,value in enumerate(values):self.history_table.setItem(i,j,QTableWidgetItem(t(value) if j>2 else value))
        verified=next((r for r in rows if r['status']=='verified'),None)
        self.home_stats[2].setText(verified['date'].replace('T',' ')[:16] if verified else 'None yet')
        if verified and self._last_record is None and not self._guide_blocked:self._last_record=verified['id'];self._last_version=verified['firmware'] or ''
    def _render_guide(self):
        version=self._last_version or (self.device.version if self.device else '')
        steps=instructions(version)
        if not self._last_record:steps[0]='Start by loading an amiibo and verifying its readback on the Load page.'
        self._guide_step=max(0,min(self._guide_step,len(steps)-1));self.guide_version.setText('FIRMWARE GUIDE · '+(version or 'UNKNOWN VERSION'))
        self.guide_number.setText(f'Step {self._guide_step+1} / {len(steps)}');self.guide_text.setText(steps[self._guide_step])
        self.guide_prev.setEnabled(self._guide_step>0);self.guide_next.setEnabled(self._guide_step<len(steps)-1)
        self.game_ok.setEnabled(bool(self._last_record));self.game_fail.setEnabled(bool(self._last_record))
    def guide_move(self,delta):self._guide_step+=delta;self._render_guide()
    def game_feedback(self,result):
        if self._last_record:
            self.library.game_result(self._last_record,result);self.game_status.setText('You reported successful recognition in the game.' if result=='recognized' else 'You reported a failed scan. See the troubleshooting tips below.');self.refresh_history()
    def set_totk_rewards(self,value):self.library.set_setting('show_totk_rewards',value);self.render_cards()
    def change_language(self):
        code=self.language_combo.currentData();set_language(code);self.library.set_setting('language',code)
        for child in self.findChildren(TranslatedLabel):child.retranslate()
        for child in self.findChildren(TranslatedButton):child.retranslate()
        self.totk_rewards.setText(t('Show TOTK rewards'));self.online.setText(t('Enable online metadata and artwork (optional)'))
        self.favorites.setText(t('Favorites'));self.search.setPlaceholderText(t('Search amiibo or rewards…'))
        self.port_combo.setPlaceholderText(t('No Pico in configuration mode'));self.tag_combo.setPlaceholderText(t('Import an amiibo into your library'))
        self.mode_combo.setItemText(0,t('Single amiibo (replace playlist)'));self.mode_combo.setItemText(1,t('Checked amiibo playlist'))
        self.history_table.setHorizontalHeaderLabels([t(x) for x in ('Date','Amiibo','Port','Verification','Game')])
        self.refresh_library();self.refresh_history();self._update_device_ui();self._render_guide()
    def set_online(self,value):self.library.set_setting('online_metadata',value);self.metadata_button.setEnabled(value)
    def refresh_metadata(self):
        if not self.online.isChecked() or 'metadata' in self._tasks:return
        def fetch(_):
            catalog=Metadata(self.library.cache);count=catalog.refresh()
            for tag in self.library.all()[:20]:
                try:catalog.fetch_image(tag)
                except (OSError,ValueError):pass
            return count
        def done(count):self.metadata=Metadata(self.library.cache);self.refresh_library();QMessageBox.information(self,'Local catalog',f'{count} public entries cached. Your library remains available offline.')
        def failed(_):QMessageBox.warning(self,'Catalog unavailable','The public source is unavailable or its format has changed. Your local amiibo remain usable; no private files were uploaded.')
        self._start('metadata',fetch,done,failed)
    def export_log(self):
        path,_=QFileDialog.getSaveFileName(self,t('Export diagnostics'),'PicoAmiibo-diagnostic.json',t('JSON log (*.json)'))
        if path:
            try:self.library.export_log(path,{'device':self.device.to_dict() if self.device else None,'protocol_confirmed':bool(self.probe),'error':self._error_message})
            except OSError:QMessageBox.warning(self,'Export failed','Cannot write this log. Choose a writable folder.')
    def open_firmwares(self):
        root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[2]
        target=root/'firmware'
        if not target.is_dir():QMessageBox.information(self,'Recovery firmware','The firmware folder is not included in this copy. Use the complete portable distribution.')
        else:QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'grid') and self.pages.currentIndex()==1:self.render_cards()
    def closeEvent(self,event):
        if 'upload' in self._tasks:
            QMessageBox.information(self,'Operation in progress','Wait for verification to finish or use Cancel operation before closing.');event.ignore();return
        if self._tasks:
            self._closing=True;self.timer.stop();self.setEnabled(False);event.ignore();return
        self.library.set_setting('window_size',[self.width(),self.height()]);self.timer.stop();event.accept()
