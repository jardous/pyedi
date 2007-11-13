#!/usr/bin/python
# -*- coding: utf-8 -*-

# #####################################################################
# Copyright (c) 2007 Jiří Popek <jiri.popek@gmail.com>
#
# name        : pyedi
# description : Python programming editor
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LICENSE:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# author : Jiří Popek
# email  : jiri.popek@gmail.com
# date   : 7.11.2007
#
# $Rev$:     Revision of last commit
# $Author$:  Author of last commit
# $Date$:    Date of last commit
# #####################################################################

import sys, string, os
from qt import *
import qtext
from qtext import QextScintilla as qs, QSCINTILLA_VERSION_STR

__author__ = u'jiri.popek@gmail.com (Jiří Popek)'

FONT_SIZE = 10
eolM = {0:'\r\n', 1:'\r', 2:'\n'}

VERSION = '0.0.1'
APPNAME = 'pyedi'

INDENT_WIDTH = 4


class QSci(qs):
    
    def __init__(self, parent, filename):
        qtext.QextScintilla.__init__(self, parent)
        self.filename = filename
        self.lex = None
        self.SendScintilla(qs.SCI_SETHSCROLLBAR)
        self.dnd = False
        
        if filename:
            self.loadDocument(filename)
        
        self.SendScintilla(qs.SCI_ASSIGNCMDKEY, qs.SCK_TAB + (qs.SCMOD_CTRL<<16), qs.SCI_BACKTAB)
        self.connect(self, SIGNAL("textChanged()"), self.textChanged)
    
    def textChanged(self):
        self.setModified(True)
        self.setTabLabel()
    
    def setTabLabel(self):
        tw = qApp.mainWidget().tab_widget
        
        if not self.filename: return
        
        if self.isUndoAvailable():#isModified(): #TODO: not reliable - WHY?
            tw.setTabLabel(self, '* ' + os.path.basename(self.filename))
        else:
            tw.setTabLabel(self, os.path.basename(self.filename))
    
    def eventFilter(self, object, event):
        used = 0
        if event.type() == QEvent.DragEnter:
            used = self.dragEnterEvent(event)
        elif event.type() == QEvent.DragMove:
            used = self.dragMoveEvent(event)
        elif event.type() == QEvent.DragLeave:
            used = self.dragLeaveEvent(event)
        elif event.type() == QEvent.Drop:
            used = self.dropEvent(event)
        if not used:
            used = qs.eventFilter(self, object, event)
        return used
    
    def loadDocument(self, filename):
        self.filename = filename
        try:
            f = open(filename, 'r')
        except:
            return
        self.setText(f.read())
        f.close()
        
        self.setModified(False)
        self.setAutoLexer()

    def lineDuplicate(self):
        self.SendScintilla(qs.SCI_LINEDUPLICATE)
    
    def uppercase(self):
        self.SendScintilla(qs.SCI_UPPERCASE)
    
    def lowercase(self):
        self.SendScintilla(qs.SCI_LOWERCASE)
    
    def setMargins(self):
        if self.marginLineNumbers(0):
            self.setMarginWidth(0, len(str(self.lines()))*FONT_SIZE)
        else:
            self.setMarginWidth(0, 0)
        self.setMarginWidth(1, 0)
    
    def setAutoLexer(self):
        basename = ext = ''
        if self.filename:
            basename, ext = os.path.splitext(self.filename)
        
        if ext in ('.py', '.spy'):
            self.lex = qtext.QextScintillaLexerPython(self)
            self.lex.setIndentationWarning(qtext.QextScintillaLexerPython.Inconsistent)
            self.lex.setFoldComments(True)
            self.lex.setFoldQuotes(True)
            self.lex.commentString = '#'
            self.lex.blockCommentStrings = None
        elif ext in ('.html', '.xml', '.svg', '.kid'):
            self.lex = qtext.QextScintillaLexerHTML(self)
            self.lex.commentString = None
            self.lex.blockCommentStrings = ('<!--', '-->')
        elif ext in ('.c', '.cc', '.cpp', '.h', '.hh'):
            self.lex = qtext.QextScintillaLexerCPP(self)
            self.lex.commentString = '//'
            self.lex.blockCommentStrings = ('/*', '*/')
        elif basename in ['Makefile']:
            self.lex = qtext.QextScintillaLexerMakefile(self)
            self.lex.commentString = '#'
            self.lex.blockCommentStrings = None
        elif ext in ('.sh', '.cfg'):
            self.lex = qtext.QextScintillaLexerBash(self)
            self.lex.commentString = '#'
            self.lex.blockCommentString = None
        elif ext in ('.java', ):
            self.lex = qtext.QextScintillaLexerJava(self)
            self.lex.commentString = '//'
            self.lex.blockCommentStrings = ('/*', '*/')
        elif ext in ('.js', ):
            self.lex = qtext.QextScintillaLexerJavaScript(self)
            self.lex.commentString = '#'
            self.lex.blockCommentStrings = ('/*', '*/')
        elif ext in ('.css', ):
            self.lex = qtext.QextScintillaLexerCSS(self)
            self.lex.commentString = None
            self.lex.blockCommentStrings = ('/*', '*/')
        
        font = QFont("Monospace", FONT_SIZE)
        
        if self.lex:
            self.lex.setDefaultFont(font)
            self.setLexer(self.lex)
        
        # a little hack - set font for comments
        for style in range(0, 12):
            self.SendScintilla(qs.SCI_STYLESETFONT, style, "monospace")
            self.SendScintilla(qs.SCI_STYLESETSIZE, style, FONT_SIZE)
        
        self.setUtf8(1)
        self.setBraceMatching(qs.SloppyBraceMatch)
        self.setAutoIndent(True)
        self.setIndentationWidth(INDENT_WIDTH)
        self.setIndentationGuides(True)
        self.setWhitespaceVisibility(qs.WsVisible)
        self.setIndentationsUseTabs(0)
        self.setAutoCompletionThreshold(1)
        self.setWrapMode(qs.WrapWord)
        self.setFolding(qs.PlainFoldStyle)
        self.setTabIndents(True)
        self.setBackspaceUnindents(True)
        self.setMargins()
    
    def checkSyntax(self):
        import re
        eline = None
        ecolumn = 0
        edescr = ''
        doc = self.text()
        
        if isinstance(self.lex, qtext.QextScintillaLexerPython):
            import compiler
            try:
                compiler.parse(str(self.text().utf8()))
            except Exception, detail:
                match = re.match('^(.+) \(line (\d+)\)$', str(detail))
                if match:
                    edescr, eline = match.groups()
                    eline = int(eline) - 1
            
        elif isinstance(self.lex, qtext.QextScintillaLexerHTML):
            from kid import compiler #TODO: check kid installed
            from cStringIO import StringIO
            t = StringIO(str(self.text().utf8()))
            
            try:
                codeobject = compiler.compile(source=t)
            except Exception, detail:
                detail = str(detail).strip().split('\n')[-1]
                match = re.match('(.+): line (\d+), column (\d+)$', detail)
                if match:
                    edescr, eline, ecolumn = match.groups()
                    eline, ecolumn = int(eline) - 1, int(ecolumn)
            
        else:
            self.emit(PYSIGNAL('status_message'), ('Only Python and XML syntax check available', 2000))
        
        if eline != None:
            self.setSelection(eline, ecolumn, eline, self.lineLength(eline)-len(eolM[self.eolMode()]))
            self.ensureLineVisible(eline)
            self.ensureCursorVisible()
            self.emit(PYSIGNAL('status_message'), (edescr, 2000))
        else:
            self.emit(PYSIGNAL('status_message'), ('Syntax ok', 2000))
    
    def convertEols(self, param):
        self.SendScintilla(qs.SCI_CONVERTEOLS, param)
        self.SendScintilla(qs.SCI_SETEOLMODE, param)
        self.setModified(True)
        self.emit(PYSIGNAL('status_message'), ({0:'Win CRLF', 1:'MAC CR', 2:'Unix LF'}[param]+' end of line mode set', 2000))
    
    def comment(self):
        """ comment out the selected text or current line """
        if not self.lex:
            return
        
        commentStr = self.lex.commentString
        bCommentStr = self.lex.blockCommentStrings
        
        self.beginUndoAction()
        if not self.hasSelectedText():
            line, index = self.getCursorPosition()
            if commentStr:
                self.insertAt(commentStr, line, 0)
            else:
                self.insertAt(bCommentStr[1], line+1, 0)
                self.insertAt(bCommentStr[0], line, 0)
        else:
            # get the selection boundaries
            lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
            if indexTo == 0:
                endLine = lineTo - 1
            else:
                endLine = lineTo
            
            ll = self.lineLength(endLine)
            if bCommentStr:
                self.insertAt(bCommentStr[1], endLine, ll)
                self.insertAt(bCommentStr[0], lineFrom, 0)
            elif commentStr:
                # iterate over the lines
                for line in range(lineFrom, endLine+1):
                    self.insertAt(commentStr, line, 0)
            
            # change the selection accordingly
            self.setSelection(lineFrom, 0, endLine+1, 0)
        
        self.endUndoAction()
    
    def marginsWidth(self):
        return self.marginWidth(0) + self.marginWidth(1) + self.marginWidth(2)
    
    def contextMenuEvent(self, evt):
        evt.accept()
        if evt.x() > self.marginsWidth():
            self.menu.popup(evt.globalPos())
    
    def find(self):
        """ find next occurence of text starting from current position """
        dt = self.selectedText()
        x = dt#[:dt.find(eolM[self.eolMode()])]
        line, index = self.getCursorPosition()
        text, res = QInputDialog.getText(APPNAME + " - Find text", "Enter text or re to find",
                                QLineEdit.Normal, x)
        if res:
            if not self.findFirst(text, 1, 0, line, index):
                self.emit(PYSIGNAL('status_message'), (text + ' not found', 2000))
    
    def saveRequest(self):
        if not self.filename:
            return self.saveAs()
        
        if self.isModified():
            self.save()
        else:
            self.emit(PYSIGNAL('status_message'), ('%s not modified' % (self.filename or ''), 2000))
            self.save()  # isModified not reliable - WHY?
    
    def save(self):
        try:
            f = open(self.filename, 'w+')
        except:
            self.emit(PYSIGNAL('status_message'), ('Can not write to %s' % (self.filename or ''), 2000))
            return
        
        f.write(str(self.text().utf8()))
        f.close()
        
        self.setModified(False)
        self.setTabLabel()
        self.emit(PYSIGNAL('status_message'), ('File %s saved' % (self.filename or ''), 2000))
    
    def saveAs(self):
        fn = QFileDialog.getSaveFileName(self.filename or '', '', self)
        if not fn.isEmpty():
            self.filename = unicode(fn)
            self.save()
            self.setAutoLexer()
            return True
        else:
            self.emit(PYSIGNAL('status_message'), ('Saving aborted', 2000))
            return False
    
    def close(self):
        if not self.isModified():
            return True
        
        res = QMessageBox.question(self, APPNAME + ' - save', 'The document\n\n' + (self.filename or 'Untitled.txt') +
            '\n\nhas been changed since the last save.\nDo you want to save it?',
            'Save', 'Cancel', 'Leave Anyway', 0, 1)
        
        if res == 0:
            if self.filename:
                return self.save()
            else:
                return self.saveAs()
        elif res == 1:
            return False
        
        return True
    
    def dragEnterEvent(self, event):
        self.dnd = QUriDrag.canDecode(event)
        event.accept(self.dnd)
        return self.dnd
    
    def dragMoveEvent(self, event):
        event.accept(self.dnd)
        return self.dnd
    
    def dragLeaveEvent(self, event):
        if self.dnd:
            self.dnd = False
            return True
        return False
    
    def dropEvent(self, event):
        if QUriDrag.canDecode(event):
            files = QStringList()
            ok = QUriDrag.decodeLocalFiles(event, files)
            if ok:
                event.acceptAction()
                for fn in files:
                    if not QFileInfo(fn).isDir():
                        qApp.mainWidget().newDoc(unicode(fn))
                    else:
                        self.emit(PYSIGNAL('status_message'), (fn + ' is not a file', 2000))
            self.dnd = False
            return True
        return False



class ApplicationWindow(QMainWindow):
    def __init__(self, caption=APPNAME):
        QMainWindow.__init__(self, None, caption, Qt.WDestructiveClose)
        self.printer = QPrinter()
        
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        self.statusMessage('Ready', 2000)
        
        settings = QSettings()
        settings.setPath('popeksoft', APPNAME)
        width = settings.readNumEntry('/geometry/width', 800)[0]
        height = settings.readNumEntry('/geometry/height', 600)[0]
        
        self.resize(width, height)
        self.clearWState(Qt.WState_Polished)
        
        def ct():
            return self.tab_widget.currentPage()
        
        self.fileNewAction = QAction("New",Qt.CTRL+Qt.Key_N,self)
        self.fileOpenAction = QAction("Open",Qt.CTRL+Qt.Key_O,self)
        self.fileCloseAction = QAction("Close",Qt.CTRL+Qt.Key_W,self)
        self.fileSaveAction = QAction("Save",Qt.CTRL+Qt.Key_S,self)
        self.fileSaveAsAction = QAction("Save As",Qt.CTRL+Qt.SHIFT+Qt.Key_S,self)
        self.filePrintAction = QAction("Print",Qt.CTRL+Qt.Key_P,self)
        self.fileExitAction = QAction("Exit",Qt.CTRL+Qt.Key_Q,self)
        self.editUndoAction = QAction("Undo",Qt.CTRL+Qt.Key_Z,self)
        self.editRedoAction = QAction("Redo",Qt.CTRL+Qt.SHIFT+Qt.Key_Z,self)
        self.editCutAction = QAction("Cut",Qt.CTRL+Qt.Key_X,self)
        self.editCopyAction = QAction("Copy",Qt.CTRL+Qt.Key_C,self)
        self.editPasteAction = QAction("Paste",Qt.CTRL+Qt.Key_V,self)
        self.editFindAction = QAction("Find",Qt.CTRL+Qt.Key_F,self)
        self.editFindNextAction = QAction("Find next",Qt.Key_F3,self)
        
        self.editDuplLineAction = QAction("Duplicate line",Qt.CTRL+Qt.Key_D,self)
        self.editCommentAction = QAction("Comment",Qt.CTRL+Qt.Key_E,self)
        self.editUncommentAction = QAction("Unomment",Qt.CTRL+Qt.SHIFT+Qt.Key_E,self)
        self.editUppercaseAction = QAction("UPPERCASE",Qt.CTRL+Qt.Key_U,self)
        self.editLowercaseAction = QAction("lowercase",Qt.CTRL+Qt.SHIFT+Qt.Key_U,self)
        
        self.editSelAllAction = QAction('Select all',Qt.CTRL+Qt.Key_A,self)
        
        self.editCheckSyntaxAction = QAction("Check syntax",Qt.ALT+Qt.Key_X,self)
        
        self.editShowEOLsAction = QAction("show EOLs",Qt.ALT+Qt.Key_Z,self)
        self.editUnixLFAction = QAction("Unix LF",Qt.ALT+Qt.Key_C,self)
        self.editWinCRLFAction = QAction("Win CRLF",Qt.ALT+Qt.Key_V,self)
        self.editMacCFAction = QAction("MAC CR",Qt.ALT+Qt.Key_B,self)
         
        self.connect(self.fileNewAction,SIGNAL("activated()"),self.newDoc)
        self.connect(self.fileOpenAction,SIGNAL("activated()"),self.fileOpen)
        self.connect(self.fileSaveAction,SIGNAL("activated()"),lambda: ct().saveRequest())
        self.connect(self.fileSaveAsAction,SIGNAL("activated()"),lambda: ct().saveAs())
        self.connect(self.filePrintAction,SIGNAL("activated()"),self.filePrint)
        self.connect(self.fileExitAction,SIGNAL("activated()"),self.fileExit)
        self.connect(self.editUndoAction,SIGNAL("activated()"),lambda: ct().undo())
        self.connect(self.editRedoAction,SIGNAL("activated()"),lambda: ct().redo())
        self.connect(self.editCutAction,SIGNAL("activated()"),lambda: ct().cut())
        self.connect(self.editCopyAction,SIGNAL("activated()"),lambda: ct().copy())
        self.connect(self.editPasteAction,SIGNAL("activated()"),lambda: ct().paste())
        self.connect(self.editFindAction,SIGNAL("activated()"),lambda: ct().find())
        self.connect(self.editFindNextAction,SIGNAL("activated()"),lambda: ct().findNext())
        
        self.connect(self.editDuplLineAction,SIGNAL("activated()"),lambda: ct().lineDuplicate())
        self.connect(self.editCommentAction,SIGNAL("activated()"),lambda: ct().comment())
        self.connect(self.editUncommentAction,SIGNAL("activated()"),lambda: ct().uncomment())
        self.connect(self.editUppercaseAction,SIGNAL("activated()"),lambda: ct().uppercase())
        self.connect(self.editLowercaseAction,SIGNAL("activated()"),lambda: ct().lowercase())
        
        self.connect(self.editSelAllAction,SIGNAL("activated()"),lambda: ct().selectAll())
        
        self.connect(self.editCheckSyntaxAction,SIGNAL("activated()"),lambda: ct().checkSyntax())
        
        self.connect(self.editShowEOLsAction,SIGNAL("activated()"),lambda: ct().setEolVisibility(not ct().eolVisibility()))
        self.connect(self.editUnixLFAction,SIGNAL("activated()"),lambda: ct().convertEols(qs.SC_EOL_LF))
        self.connect(self.editWinCRLFAction,SIGNAL("activated()"),lambda: ct().convertEols(qs.SC_EOL_CRLF))
        self.connect(self.editMacCFAction,SIGNAL("activated()"),lambda: ct().convertEols(qs.SC_EOL_CR))
        
        #self.connect(self.tab_widget, SIGNAL("currentChanged(QWidget*)"), self.currentTabChanged)
    
    def fileOpen(self):
        filename = QFileDialog.getOpenFileName(QString.null, QString.null, self)
        if filename.isEmpty():
            self.statusMessage('Loading aborted', 2000)
            return
        
        filename = unicode(filename)
        self.newDoc(filename)
        self.statusBar().message('Loaded document %s' % filename, 2000)
    
    def newDoc(self, filename=None):
        tab = QSci(self, filename)
        self.connect(tab, PYSIGNAL('status_message'), self.statusMessage)
        if not filename:
            filename = 'Untitled.txt'
        self.tab_widget.addTab(tab, os.path.basename(filename))
        self.tab_widget.showPage(tab)
        tab.setFocus()
    
    def statusMessage(self, text, t=2000):
        self.statusBar().message(text, t)
    
    def currentTabChanged (self, tab):
        tab.setFocus()
        self.statusMessage(tab.filename, 1000)
    
    def closeCurrentTab(self):
        print 'closeCurrentTab'
        if self.tab_widget.count()==1: return
        
        tab = self.tab_widget.currentPage()
        if tab.close():
            self.tab_widget.removePage(tab)
            del tab
            return True
        return False
    
    def filePrint(self):
        #TODO: need change
        Margin = 10
        pageNo = 1
        
        if self.printer.setup(self):
            self.statusBar().message('Printing...')
            
            p = QPainter()
            p.begin(self.printer)
            p.setFont(self.e.font())
            yPos = 0
            fm = p.fontMetrics()
            metrics = QPaintDeviceMetrics(self.printer)
            
            for i in range(self.e.numLines):
                if Margin + yPos > metrics.height() - Margin:
                    pageNo = pageNo + 1
                    self.statusBar().message('Printing (page %d)...' % (pageNo))
                    self.printer.newPage()
                    yPos = 0
                p.drawText(Margin,Margin + yPos,metrics.width(), fm.lineSpacing(),
                                Qt.ExpandTabs | Qt.DontClip, self.e.textLine(i))
                yPos = yPos + fm.lineSpacing()
            
            p.end()
            self.statusBar().message('Printing completed', 2000)
        else:
            self.statusBar().message('Printing aborted', 2000)
    
    def closeEvent(self, ce):
        if self.fileExit():
            ce.accept()
        ce.ignore()
    
    def fileExit(self):
        tab = self.tab_widget.currentPage()
        while tab:
            if not tab.close():
                return False
            self.tab_widget.removePage(tab)
            del tab
            tab = self.tab_widget.currentPage()
        
        settings = QSettings()
        settings.setPath('popeksoft', APPNAME)
        settings.writeEntry('/geometry/width', self.width())
        settings.writeEntry('/geometry/height', self.height())
        
        qApp.quit()


icondata = '''\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00\x1e\x08\x06\x00\x00\x00M\n\x1c)\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00\tpHYs\x00\x00\x00\xee\x00\x00\x00\xee\x01\x06\xd6\xb24\x00\x00\x00\x19tEXtSoftware\x00www.inkscape.org\x9b\xee<\x1a\x00\x00\x05=IDATH\x89\xb5\x96[LTW\x14\x86\xff=W\xc6\xa2\xed\x08\x1d\x1d\x06\x82\xe5\xa2\x88\xb4V\xb1\n\x14\xa1\xb1\xf8Pj%&\xb4QkB\xd3V\xa3\xdc\xda*I\x1fj4\x9a46\xd6\x9aX\xa5\xd1\x04\x1b%i|05\xb1\xb5\xc6K\xda\xa8EH\xa9R\x8b\n\xf6B\x11D\x91\xfb0\\\x86\xd9s\xe6\xfc}\x98 \x8c\x830C\xcbI\xd6\xcb\xd9{\x7f\xeb;g\xad\xb3\xf7\x11$\x11\xece\x12"+J\xab]\x9b\x91\x95\x95\x16\x11\x1e\xfe\xb4\xc7\xe3\xc1\x8f\'O:\x9d\x1e\xcf\xd0\x10\xf0{\x13\xf0\x8d\x0b\xb8@R\x99\x10F2\xa0\x00 \xcc\xc0\xfa\xd7\x12\x13\xef\\?z\xd4\xe5\xea\xe8\xa0B\xd2MR^\xbfNi6S\x02\xec<x\x907\x8f\x1dsoHOo\x9e\x05l\x06\xa0\x1d\x97\x1b`\xf2\x19\xd1\xc0O_\xc7\xc5\xf5\xb9\xeb\xea\xa8\xf4\xf6\xd2\xad\xaa\x94v;eA\x01\xa5FC\tP\xeat\x94\xdd\xdd\x94$\xa5\xaa\xb2\xbe\xbc\xdc\xbd,<\xbc\x1e\xc0\xdcI\x0b\x00\x88_\x16\x1e\xfe\xc7\xdf99\xaa\xb2q#\xdd\x0b\x17Rj\xb5\x94F#eh\xa87\xf1\xe8\xc8\xcf\xa7lk\xa3lj\xa2\xcc\xcbc\xabF\xc3W\x81\x96(\xe0\xdd\xa0\x05\xc2\x807\xdeKIy\xd8[XHe\xcd\x1a\xca\x90\x10\xff\x84c\x85VKi0P\xea\xf5\x94\x9b6Qn\xdd\xca\x9dqq=\x91@q\xc0\x02Q\xc0\xee\x03\xb9\xb9v\xe5\xc1\x03\xba\xeb\xea(\xd7\xae\r,\xf9\xe88~\xdc[\x0e\x92RJ\x96o\xdb\xe6\xb0\x00oM(`\x03>?\xb6dI\x9f\xe2px\x9b\x8c\xa4T\x14\xcaU\xabF\xe03fP\x1e>LY[K\xb9}\xfbH\x1f\x8c\x8e\xfb\xf7G\x04H\xca\xc6F\xae\x04\x1e\x84\x02\x99O\x14\x98\x01\xac\xfch\xde\xbc\x0e\xa5\xb4\x94\xca\xe8\xc5$eY\x99\x17,\x04\xe5\xb9s\xbec{\xf6\xf8\x0btv\xfa\xce\xb9}\x9b\x0e\x80K\x81f\x00\xf3\xfc\x04\x00\xcc~=6\xf6\x9e\xb3\xa0\x80\xca\x91#\xbe\x8bI\xef+\x05(cb\xfc\xc7H\xca\x9c\x1c_\x81\xd2R\x9f\x12\xc8\xd4TJ\x8d\x86\xed\xeb\xd6q\x99\xd5Z\xed#\x00@\xfb\x82\xd9\xfc\xeb\xc3\xfc|*\xc5\xc5t\xa7\xa5Q\x9e?O\xe9tz\x01\x97/SZ\xad^\xf0\xea\xd5c\x0b\x9c9\xe3+\xa0\xd7Sn\xdeLYTD\x99\x9c\xec\xbdWVFI\xf2\xb7\xd3\xa7]\x06 \xf3\x91@$p\xa8\xe9\xd4)\xb7\xa2(T*+\xbd\x8b\x87;::\xda\x17\x9c\x9d=\xb6\xc0\xd9\xb3\x137\xe6p_\xb8\xddL\x8f\x89\xb93\xfc\xf4\xc9\xdf\xee\xda\xd5\xa7\x90#\xbb\x9b\xc52>\xe8\xda5\xdf\xe4CC\x94YYO\x9c\xdf\x03\xf0*\xc0\x8byy\xaeCEE]\xcbm\xb6\x1bQ\xc0\x87\x82$\xd2l\xb6\x8a+w\xef\xbe,\xf4z\x00\x80\xda\xd0\x00\xc4\xc7\x03\xe3\x9d\x13\t\t\xc0\x8e\x1d\x80\xcd\x06TU\x01\xe5\xe5@]\x1d\x00\xa0\x1d@\r\xc0\x9f\x81\xce_\x80\xc1\x1e\xa0o\x10hw\x01\xd5-@\x05\x80J\x92=\xc3\xa8\x05g\xf7\xef\xef\x1f~z\x85\xa4,)\t\xf8[\xef\x02\xf8\x83\x10\xdc\x1dff\xa6\xd1\xa0.\x00jc\x81\xd3f\xa0\x00\xc0\x8b\x00\xf4\xe3\xee\xb4s\x80#\xfd7o>J\xee>q\xc2\xbb\x8b=!\xe1 \xc0z\x80\x87\x9e\x9a\xc67\xa3\xa3\xf8vF*\x0f|\xb6\x93\x97.}\xc7\xa5K\x17\rM\xb4\xb5?\x1e:\x83\x10\xa9\x86\xeajx\\.\x0c\\\xbd\x8a\xc6\x92\x12\xd8\xddn8\x00\xd8\x01O+0x\x1b\xe8o\x02\xe4\x00\xd0\xdf\x0fh\x17\xa4,Ix\xe7\xe3b|\x95\x9e\n\xbd^\xf7\xa8*\xd3\xa7O\x87\x10\xc2D\xd2\x19\xc0\xa9\x0e\x00\xd0\xb9\xc8\xe6\xc5[\xb68TE\xb1\xab\xaa\xda\xad\x02].\xa0\xbd\x0fh\xeb\xf6\x96\xb3\x0b\xc0?$\xdb\x00 &f\xce\x97%\xfbv\'$%\xcd\xf7\x83-_\x9e\xa2\xad\xae\xbe\x96\x05\xe0\xfb@\x05\x04\x83\xfc!\x89\x8b{\xae\xb2\xaa\xeaB\xaa\xc1\xa0\xf7\x1b\xb3\xdb{\xb1bENMC\xc3\xdd\xe4@y\xba\x89\xa7\xf8]-\xeb\xd7\xbf/32\xd2\x0cCCCp8\xfa\xd0\xda\xda\x06\x8f\xc7\x83[\xb7\xea\x07T\x95\x17\x83\xa2\x05\xdb4$\x91\x98\x18_[Qq\x9255g\xd8\xd8x\x85Ng=\xfb\xfb\xfebnnv+\x00K0\xacI\t$%\xcd\xbd!\xe5\x9f\x1c\x1d\xbd\xf6\x06VW_P##g\x7f\x12\x0cK3\x89\x12\x80\x84x\xfc\x9eV\xa7"\xca\x16\'l6\xeb&!\x84!P\xd6$\x05\xe8\'\xa0\xd3\x11\xa4\xc0\x17\xfb>\x8d\x88\x8c\x9c\xfd\xc1\x94\n\x00\xfe\x02\x1a\x8d7bc\xe6\xebf\xce4\x17\n!\x8cS&`4\x1a\xc6\x84\xeb\r*H`\xef\xde\x9dV\x8b%<\x7fJ\x04\x84\x10\x1a\x93)$dL\xb1\x10\x15\x00\xb0x\xd1K\xfa\xb0\xb0g\xb6\x08!\xfc\xde\xd4\x7f\x16\x00\xf0lD\xc4,\xedX\x03z=\xa1\xd1\x00\x8a[\x83\r\x1br\xc3\x00<?\x15\x02\xce\xc1A\xa7g\xac\x01!\xbce\x00\x80\xcc\x8cT\xb3\xd5j\xc9\xfe\xdf\x05H:\x1a\x1b\xef\xb5\xb5\xb4\xb4\xc2\xe3\xf1\xf70\x99T\x0c\x0cv`\xeb\xb6\x1d\xf7\x8dFC\xfdD\xbc\xa0\xcf\x02\x00\xb0Z-\xaf\x84\x86N\xcb\x07`\x0b\t1N3\x99L!&\x93\xd1\xe8rI\xf7\xc0\x80s\xd0\xe9t6444\x17\x92|8\x11\xeb_\xd4\x8f\xe4\x00\xd4\x0cPu\x00\x00\x00\x00IEND\xaeB`\x82'''


if __name__=="__main__":
    
    app = QApplication(sys.argv)
    main_window = ApplicationWindow()
    app.setMainWidget(main_window)
    appico = QPixmap()
    appico.loadFromData(icondata, 'PNG')
    main_window.setIcon(appico)
    
    files = sys.argv[1:]
    if files:
        for f in files:
            f = os.path.abspath(f)
            main_window.newDoc(f)
    else:
        main_window.newDoc()
    
    main_window.show()
    
    app.exec_loop()