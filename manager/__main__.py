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
        QMessageBox.critical(None,'Cannot open','Cannot open local PicoAmiibo Manager data. Check the permissions of your user data folder.');return 1
    window.show()
    if args.smoke_test:
        def capture():
            result={'success':False,'usb_disabled':True,'frozen':bool(getattr(sys,'frozen',False)),'pages':[]}
            try:
                if args.screenshots:
                    args.screenshots.mkdir(parents=True,exist_ok=True)
                    for i,name in enumerate(('home','library','load','switch2','diagnostics')):
                        window.page(i);app.processEvents()
                        if not window.grab().save(str(args.screenshots/(name+'.png'))):raise OSError('Screenshot write failed')
                        result['pages'].append(name)
                    from manager.app.rewards import RewardsDialog
                    from manager.app.widgets import label
                    dialog=RewardsDialog(window.rewards,'01000000034d0902',window)
                    dialog.layout().insertWidget(1,label('TEST · Offline reference · no USB access','testBanner'))
                    dialog.show();app.processEvents()
                    if not dialog.grab().save(str(args.screenshots/'totk-rewards.png')):raise OSError('Rewards screenshot failed')
                    dialog.close();result['pages'].append('totk-rewards')
                result['success']=True
            except Exception as error:result['error']=type(error).__name__
            finally:
                (root/'smoke-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                window.close();app.exit(0 if result['success'] else 2)
        QTimer.singleShot(700,capture)
    return app.exec()

if __name__=='__main__':raise SystemExit(main())
