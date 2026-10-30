import argparse
import json
import os
from pathlib import Path
import sys
import sqlite3
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication,QMessageBox
from manager.core.library import Library
from manager.app.window import MainWindow
from manager.i18n import t

def main(argv=None):
    parser=argparse.ArgumentParser(description="PicoAmiibo Manager")
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--no-usb',action='store_true',help='Test only: never open a device')
    parser.add_argument('--smoke-test',action='store_true')
    parser.add_argument('--screenshots',type=Path)
    args=parser.parse_args(argv)
    if args.smoke_test and not args.data_dir:parser.error('An isolated --data-dir is required for a smoke test')
    app=QApplication.instance() or QApplication(sys.argv[:1]);app.setApplicationName('PicoAmiibo Manager');app.setOrganizationName('PicoAmiibo')
    root=args.data_dir or Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'PicoAmiiboManager'
    try:window=MainWindow(Library(root),no_usb=args.no_usb or args.smoke_test,test_mode=args.smoke_test)
    except (OSError,ValueError,sqlite3.Error) as error:
        if args.smoke_test:raise
        QMessageBox.critical(None,t('Cannot open'),t('Cannot open local PicoAmiibo Manager data. Check the permissions of your user data folder.'));return 1
    window.show()
    if args.smoke_test:
        def capture():
            result={'success':False,'usb_disabled':True,'frozen':bool(getattr(sys,'frozen',False)),'pages':[]}
            try:
                if args.screenshots:
                    args.screenshots.mkdir(parents=True,exist_ok=True)
                    from manager.app.rewards import RewardsDialog
                    from manager.app.widgets import label
                    from PySide6.QtTest import QTest
                    for code in ('en','fr'):
                        window.language_combo.setCurrentIndex(window.language_combo.findData(code))
                        for i,name in enumerate(('home','library','load','switch2','diagnostics')):
                            window.mode_combo.setCurrentIndex(0);window.page(i);QTest.qWait(80)
                            file=code+'-'+name
                            if not window.grab().save(str(args.screenshots/(file+'.png'))):raise OSError('Screenshot write failed')
                            result['pages'].append(file)
                        window.check_shown();window.open_playlist();QTest.qWait(80)
                        file=code+'-playlist'
                        if not window.grab().save(str(args.screenshots/(file+'.png'))):raise OSError('Screenshot write failed')
                        result['pages'].append(file)
                        dialog=RewardsDialog(window.rewards,'01000000034d0902',window)
                        dialog.layout().insertWidget(1,label('TEST · Offline reference · no USB access','testBanner'))
                        dialog.show();QTest.qWait(80)
                        file=code+'-totk-rewards'
                        if not dialog.grab().save(str(args.screenshots/(file+'.png'))):raise OSError('Rewards screenshot failed')
                        dialog.close();result['pages'].append(file)
                    if len(result['pages'])!=14:raise ValueError('Missing bilingual captures')
                result['success']=True
            except Exception as error:result['error']=type(error).__name__
            finally:
                (root/'smoke-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                window.close();app.exit(0 if result['success'] else 2)
        QTimer.singleShot(700,capture)
    return app.exec()

if __name__=='__main__':raise SystemExit(main())
