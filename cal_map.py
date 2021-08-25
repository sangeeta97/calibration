# -*- encoding:utf-8 -*-
import xlrd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import re
import sys, os
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import *
import pandas as pd
import re
import numpy as np
from collections import defaultdict
from calibration import *
from PyQt5.uic import loadUiType
import tempfile




def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)



FORM_CLASS, _= loadUiType(resource_path("cal.ui"))# use ui reference to load the widgets



class Main(QDialog, FORM_CLASS):


    '''The goal of this tool is to create a GUI that
        allows the user to quickly create, select and
        view the kml files'''    # create class instance

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        self.setupUi(self)
        self.launcher = Quantitation()
        self.toolButton_2.setEnabled(False)
        self.toolButton_3.setEnabled(False)
        self.listWidget.setAlternatingRowColors(True)
        self.temporary= tempfile.TemporaryDirectory()
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)
        self.Handel_Buttons()



    def closeEvent(self, event):
         close = QMessageBox.question(self, "QUIT", "Are you sure you want to close the program?",QMessageBox.Yes | QMessageBox.No)
         if close == QMessageBox.Yes:
             self.listWidget.clear()
             self.temporary.cleanup()
             event.accept()
         else:
             event.ignore()


    #======= SETUP UI =================================

    def Handel_Buttons(self):
        self.toolButton.clicked.connect(self.open_file)
        self.toolButton_2.clicked.connect(self.run_file)
        self.toolButton_3.clicked.connect(self.save_file)
        self.toolButton_4.clicked.connect(self.clear)
        self.listWidget.itemClicked.connect(self.Clicked)



    def run_file(self):
        self.launcher.extrapolate()
        self.listWidget.addItem('quan results.csv')
        self.listWidget.addItem('calibration results.csv')
        for x in self.launcher.result_image.keys():
            self.listWidget.addItem(f'{x}.png')
            f= self.temporary
            outfile1 = os.path.join(f.name, f'{x}.png')
            self.launcher.result_image[x].savefig(outfile1)
        outtext1 = os.path.join(f.name, 'quan.csv')
        self.launcher.result_files['result'].to_csv(outtext1)
        outtext2 = os.path.join(f.name, 'cal.csv')
        self.launcher.result_files['calibration'].to_csv(outtext2)
        self.toolButton_3.setEnabled(True)




    def open_file(self):
        msg = '1) Select the excel file with sample and cal area values'
        msg += '2) Select a cal file with concentration in ppm values'
        QMessageBox.information(self, 'Add input files', msg)
        sel = 'Select excel file'
        area = self.file_dialog(sel, ".")
        if area:
            path = os.path.split(area)[0]
            msg = 'Select conc excel file'
            ppm = self.file_dialog(msg, path)
            self.launcher.filepath(area, ppm)
            self.toolButton_2.setEnabled(True)


    def file_dialog(self, msg, path):
        return QFileDialog.getOpenFileName(self, msg, path)[0]


    def save_file(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            path_text= QDir.toNativeSeparators(str(filenames[0]))
            self.launcher.savepath(path_text)
            self.launcher.result_files['result'].to_csv(os.path.join(path_text, 'result_quantitation.csv'))
            self.launcher.result_files['calibration'].to_csv(os.path.join(path_text, 'result_calibration.csv'))
            for key in self.launcher.result_image.keys():
                self.launcher.result_image[key].savefig(os.path.join(path_text, f'{key}.png'))


    def clear(self):
        self.toolButton_2.setEnabled(False)
        self.toolButton_3.setEnabled(False)
        self.listWidget.clear()
        self.plainTextEdit.clear()
        self.launcher.result_files = defaultdict(lambda: None)
        self.launcher.result_image = defaultdict(lambda: None)
        self.launcher.input_files= defaultdict(lambda: None)



    def Clicked(self, name):
        name= name.text()
        if name.startswith('quan'):
            xx= os.path.join(self.temporary.name, 'quan.csv')
            mat= open(xx).read()
            self.plainTextEdit.setPlainText(mat)


        if name.startswith('calibration'):
            xx= os.path.join(self.temporary.name, 'cal.csv')
            mat= open(xx).read()
            self.plainTextEdit.setPlainText(mat)


        for n in self.launcher.result_files['names']:
            if name.endswith(f'{n}.png'):
                import webbrowser
                new= 2
                final= os.path.join(self.temporary.name, f'{n}.png')
                url = f"file://{final}"
                webbrowser.open(url,new=new)


def main1():
    app=QApplication(sys.argv)
    window=Main()
    window.show()
    QApplication.processEvents()
    app.exec_()



if __name__=='__main__':
    main1()
