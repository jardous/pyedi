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
from math import log

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.Qsci import *
from PyQt4.Qsci import QsciScintillaBase as qs

try:
    import psyco
    psyco.full() #PSYCO speeds up Python
except:
    pass

__author__ = u'jiri.popek@gmail.com (Jiří Popek)'

FONT_SIZE = 10
EOL_UNIX, EOL_WIN, EOL_MAC = 2, 0, 1
eolM = {EOL_WIN:'\r\n', EOL_MAC:'\r', EOL_UNIX:'\n'}

VERSION = '0.1.2'
APPNAME = 'pyedi'

INDENT_WIDTH = 4

DEFAULT_FILENAME = 'Untitled.txt'

main_window = None

print "QScintilla version", QSCINTILLA_VERSION_STR

opening = ['(', '{', '[', "'", '"', '<']
closing = [')', '}', ']', "'", '"', '>']

class QSci(QsciScintilla):
    
    def __init__(self, parent, filename):
        QsciScintilla.__init__(self, parent)
        self.SendScintilla(qs.SCI_SETHSCROLLBAR)
        self.dnd = False
        self.filename = None
        self.mtime = 0 # time of most recent content modification
        
        if filename:
            self.filename = filename
            if os.path.exists(filename):
                self.loadDocument(filename)
        self.connect(self, SIGNAL("linesChanged()"), self.linesChanged)
        
        self.setUtf8(True)
        self.setAutoLexer()
    
    def focusInEvent(self, event):
        """ check if document has changed """
        if self.filename:
            if not os.path.exists(self.filename): return
        
        if self.filename and self.mtime != os.stat(self.filename).st_mtime:
            ret = QMessageBox.warning(self, "Reload", "Document get changed. Reload?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.loadDocument(self.filename)
            else:
                self.mtime = os.stat(self.filename).st_mtime
        QsciScintilla.focusInEvent(self, event)
    
    def keyPressEvent(self, event):
        t = unicode(event.text())
        
        self.beginUndoAction()
        
        if not self.isReadOnly():
            if t and (ord(t) == 8): # backspace
                line, index = self.getCursorPosition()
                if index:
                    prev = self.text(line)[index-1]
                    if index < self.lineLength(line):
                        next = self.text(line)[index-1]
                        if (prev in opening) and (next in closing):
                            if opening.index(prev) == closing.index(next):
                                self.setCursorPosition(line, index+1)
                                QsciScintilla.keyPressEvent(self, event) # process backspace twice
            
            if t in opening:
                i = opening.index(t)
                self.insert(closing[i])
        
        QsciScintilla.keyPressEvent(self, event)
        self.endUndoAction()
    
    def loadDocument(self, filename):
        self.mtime = os.stat(filename).st_mtime
        file = QFile(filename)
        
        if not file.open(QFile.ReadOnly | QFile.Text):
            QMessageBox.warning(self, APPNAME, "Cannot read file %s:\n%s." %(filename, file.errorString()))
            return False
        
        if not os.access(filename, os.W_OK):
            self.setReadOnly(True)
        
        self.filename = filename
        instr = QTextStream(file)
        self.setUtf8(True)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.setText(instr.readAll())
        QApplication.restoreOverrideCursor()
        
        self.setModified(False)
        self.setAutoLexer()
        return True

    def lineDuplicate(self):
        self.SendScintilla(qs.SCI_LINEDUPLICATE)
    
    def uppercase(self):
        self.SendScintilla(qs.SCI_UPPERCASE)
    
    def lowercase(self):
        self.SendScintilla(qs.SCI_LOWERCASE)
    
    def setMargins(self):
        if self.marginLineNumbers(0):
            l = int(log(self.lines(), 10))
            self.setMarginWidth(0, (l+1)*FONT_SIZE)
        else:
            self.setMarginWidth(0, 0)
        self.setMarginWidth(1, 0)
    
    def setAutoLexer(self):
        basename = ext = ''
        if self.filename:
            basename, ext = os.path.splitext(os.path.basename(self.filename))
        
        self.setIndentationsUseTabs(0)
        self.setIndentationWidth(INDENT_WIDTH)
        lex = QsciLexerProperties() # set default lexer to properties
        if ext in ('.py', '.spy'):
            lex = QsciLexerPython(self)
            lex.setIndentationWarning(QsciLexerPython.Inconsistent)
            lex.setFoldComments(True)
            lex.setFoldQuotes(True)
            lex.commentString = '#'
            lex.blockCommentStrings = None
        elif ext in ('.html', '.xml', '.svg', '.kid', '.ui'):
            lex = QsciLexerHTML(self)
            lex.commentString = None
            lex.blockCommentStrings = ('<!--', '-->')
            self.setIndentationsUseTabs(1)
            self.setIndentationWidth(1)
        elif ext in ('.c', '.cc', '.cpp', '.h', '.hh'):
            lex = QsciLexerCPP(self)
            lex.commentString = '//'
            lex.blockCommentStrings = ('/*', '*/')
        elif basename in ['Makefile'] or ext in ['.mk']:
            lex = QsciLexerMakefile(self)
            lex.commentString = '#'
            lex.blockCommentStrings = None
            self.setIndentationsUseTabs(1)
            self.setIndentationWidth(1)
        elif ext in ('.sh', '.cfg'):
            lex = QsciLexerBash(self)
            lex.commentString = '#'
            lex.blockCommentString = None
        elif ext in ('.java', ):
            lex = QsciLexerJava(self)
            lex.commentString = '//'
            lex.blockCommentStrings = ('/*', '*/')
        elif ext in ('.js', ):
            lex = QsciLexerJavaScript(self)
            lex.commentString = '#'
            lex.blockCommentStrings = ('/*', '*/')
        elif ext in ('.css', ):
            lex = QsciLexerCSS(self)
            lex.commentString = None
            lex.blockCommentStrings = ('/*', '*/')
        
        font = QFont("Monospace", FONT_SIZE)
        
        lex.setDefaultFont(font)
        lex.setFont(font)
        self.setLexer(lex)
        
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setCaretWidth(2)
        self.setCaretLineVisible(True)
        self.setCaretForegroundColor(QColor(0,0,0))
        self.setAutoIndent(True)
        self.setIndentationGuides(True)
        self.setIndentationWidth(INDENT_WIDTH)
        self.setWhitespaceVisibility(QsciScintilla.WsVisible)
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionReplaceWord(True)
        self.setWrapMode(QsciScintilla.WrapWord)
        self.setFolding(QsciScintilla.PlainFoldStyle)
        self.setTabIndents(True)
        self.setBackspaceUnindents(True)
        self.setMargins()
    
    def syntaxCheck(self):
        import re
        eline = None
        ecolumn = 0
        edescr = ''
        doc = unicode(self.text())
        
        if isinstance(self.lexer(), QsciLexerPython):
            import compiler
            try:
                compiler.parse(doc)
            except Exception, detail:
                match = re.match('^(.+) \(line (\d+)\)$', str(detail))
                if match:
                    edescr, eline = match.groups()
                    eline = int(eline) - 1
            
        elif isinstance(self.lexer(), QsciLexerHTML):
            from kid import compiler #TODO: check kid installed
            from cStringIO import StringIO
            t = StringIO(doc)
            
            try:
                codeobject = compiler.compile(source=t)
            except Exception, detail:
                detail = str(detail).strip().split('\n')[-1]
                match = re.match('(.+): line (\d+), column (\d+)$', detail)
                if match:
                    edescr, eline, ecolumn = match.groups()
                    eline, ecolumn = int(eline) - 1, int(ecolumn)
            
        else:
            self.emit(SIGNAL('status_message'), 'Only Python and XML syntax check available', 2000)
        
        if eline != None:
            self.setSelection(eline, ecolumn, eline, self.lineLength(eline)-len(eolM[self.eolMode()]))
            self.ensureLineVisible(eline)
            self.ensureCursorVisible()
            self.emit(SIGNAL('status_message'), edescr, 2000)
        else:
            self.emit(SIGNAL('status_message'), 'Syntax ok', 2000)
    
    def syntaxCheckAvailable(self):
        lex = self.lexer()
        return (isinstance(lex, QsciLexerPython) or isinstance(lex, QsciLexerHTML))
    
    def convertEols(self, param):
        self.SendScintilla(qs.SCI_CONVERTEOLS, param)
        self.SendScintilla(qs.SCI_SETEOLMODE, param)
        self.setModified(True)
        self.emit(SIGNAL('status_message'), {0:'Win CRLF', 1:'MAC CR', 2:'Unix LF'}[param]+' end of line mode set', 2000)
    
    def comment(self):
        """ comment out the selected text or current line """
        lex = self.lexer()
        if not lex:
            return
        
        commentStr = lex.commentString
        selection = self.getSelection()
        self.beginUndoAction()
        if not self.hasSelectedText():
            line, index = self.getCursorPosition()
            self.insertAt(commentStr, line, 0)
            lines_to_comment.append(line)
        else:
            lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
            
            if indexTo == 0:
                endLine = lineTo - 1
            else:
                endLine = lineTo
            
            lines_to_comment = range(lineFrom, lineTo+1)
        
        newsel = list(selection)
        if commentStr:
            for line in lines_to_comment:
                self.insertAt(commentStr, line, 0)
        
            newsel[1] += len(commentStr)
            newsel[3] += len(commentStr)
        
        self.setSelection(*newsel)
        self.endUndoAction()
    
    def uncomment(self):
        """ uncomment selected lines """
        lex = self.lexer()
        if not lex:
            return
        
        commentStr = lex.commentString
        bCommentStr = lex.blockCommentStrings
        
        lines_to_uncomment = []
        selection = self.getSelection()
        self.beginUndoAction()
        if not self.hasSelectedText():
            line, index = self.getCursorPosition()
            lines_to_uncomment.append(line)
        else:
            lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
            if indexTo == 0:
                endLine = lineTo - 1
            else:
                endLine = lineTo
            
            lines_to_uncomment = range(lineFrom, lineTo+1)
        
        newsel = list(selection)
        if commentStr:
            for line in lines_to_uncomment:
                self.setSelection(line, 0, line, len(commentStr))
                if self.selectedText().toUtf8() == commentStr:
                    self.removeSelectedText()
            
            newsel[1] -= len(commentStr)
            newsel[3] -= len(commentStr)
        
        self.setSelection(*newsel)
        self.endUndoAction()
    
    def marginsWidth(self):
        return self.marginWidth(0) + self.marginWidth(1) + self.marginWidth(2)
    
    def linesChanged(self):
        l = self.lines()
        if l<2: return
        if int(log(l, 10)) > int(log(l-1, 10)):
            self.setMargins()
    
    def find(self):
        """find next occurence of text starting from current position"""
        dt = self.selectedText()
        line, index = self.getCursorPosition()
        text, res = QInputDialog.getText(self, APPNAME + " - Find text", "Enter text or re to find",
                                QLineEdit.Normal, dt)
        if res:
            if not self.findFirst(text, 1, 0, line, index):
                self.emit(SIGNAL('status_message'), text + ' not found', 2000)
    
    def saveRequest(self):
        if not self.filename:
            return self.saveAs()
        
        if self.isModified():
            self.save()
        else:
            self.emit(SIGNAL('status_message'), '%s not modified' % (self.filename or ''), 2000)
    
    def save(self):
        file = QFile(self.filename)
        if not file.open(QFile.WriteOnly | QFile.Text):
            QMessageBox.warning(self, APPNAME, "Cannot write file %s:\n%s." % (str(file.fileName()), file.errorString()))
            return False
        
        outstr = QTextStream(file)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        outstr << self.text()
        QApplication.restoreOverrideCursor()
        
        if self.isModified():
            self.setModified(False)
        else:
            self.emit(SIGNAL('modificationChanged(bool)'), False)
        
        self.emit(SIGNAL('status_message'), 'File %s saved' % (self.filename or ''), 2000)
        
        self.mtime = os.stat(self.filename).st_mtime
        
        return True
    
    def saveAs(self):
        fn = QFileDialog.getSaveFileName(self, 'Save As', self.filename or '')
        if not fn.isEmpty():
            self.filename = unicode(fn)
            self.save()
            self.setAutoLexer()
            self.setReadOnly(False)
            return True
        else:
            self.emit(SIGNAL('status_message'), 'Saving aborted', 2000)
            return False
    
    def close(self):
        if not self.isModified():
            return True
        
        res = QMessageBox.question(self, APPNAME + ' - save', 
                    'The document\n\n' + (self.filename or DEFAULT_FILENAME) +
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
        mime = event.mimeData()
        self.dnd = mime.hasUrls()
        if self.dnd:
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if self.dnd:
            event.accept()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        if self.dnd:
            self.dnd = False
            return True
        return False
    
    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            files = mime.urls()
            event.accept()

            for fn in files:
                fn = fn.toLocalFile()
                if fn.isEmpty(): continue
                if not QFileInfo(fn).isDir():
                    main_window.newDoc(unicode(fn))
                else:
                    self.emit(SIGNAL('status_message'), fn + ' is not a file', 2000)
                
            self.dnd = False
        else:
            event.ignore()



class ApplicationWindow(QMainWindow):
    def __init__(self, caption=APPNAME):
        QMainWindow.__init__(self)
        
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        
        self.createActions()
        self.createMenus()
        
        self.readSettings()
        
#        self.statusMessage('Ready', 2000)
    
    def readSettings(self):
        settings = QSettings('pyedi', APPNAME)
        pos = settings.value('/geometry/pos', QVariant(QPoint(0, 0))).toPoint()
        size = settings.value('/geometry/size', QVariant(QSize(800,600))).toSize()
        
        self.resize(size)
        self.move(pos)
    
    def writeSettings(self):
        settings = QSettings('pyedi', APPNAME)
        settings.setValue("/geometry/pos", QVariant(self.pos()))
        settings.setValue("/geometry/size", QVariant(self.size()))
    
    def save(self):
        self.tab_widget.currentWidget().saveRequest()
    def saveAs(self):
        self.tab_widget.currentWidget().saveAs()
    def undo(self):
        self.tab_widget.currentWidget().undo()
    def redo(self):
        self.tab_widget.currentWidget().redo()
    def cut(self):
        self.tab_widget.currentWidget().cut()
    def copy(self):
        self.tab_widget.currentWidget().copy()
    def paste(self):
        self.tab_widget.currentWidget().paste()
    def comment(self):
        self.tab_widget.currentWidget().comment()
    def uncomment(self):
        self.tab_widget.currentWidget().uncomment()
    def find(self):
        self.tab_widget.currentWidget().find()
    def findNext(self):
        self.tab_widget.currentWidget().findNext()
    def showEOLs(self):
        w = self.tab_widget.currentWidget()
        w.setEolVisibility(not w.eolVisibility())
    def syntaxCheck(self):
        self.tab_widget.currentWidget().syntaxCheck()
    def unixLF(self):
        self.tab_widget.currentWidget().convertEols(qs.SC_EOL_LF)
    def winCRLF(self):
        self.tab_widget.currentWidget().convertEols(qs.SC_EOL_CRLF)
    def macCR(self):
        self.tab_widget.currentWidget().convertEols(qs.SC_EOL_CR)
    def copyEnabled(self):
        return self.tab_widget.currentWidget().isCopyAvailable()
    def cutEnabled(self):
        return self.copyEnabled()
    def syntaxCheckAvailable(self):
        return self.tab_widget.currentWidget().checkSyntaxAvailable()
    def unindent(self):
        w = self.tab_widget.currentWidget()
        selection = w.getSelection()
        w.beginUndoAction()
        if not w.hasSelectedText():
            line, index = w.getCursorPosition()
            w.unindent(line)
        else:
            lineFrom, indexFrom, lineTo, indexTo = w.getSelection()
            for l in range(lineFrom, lineTo+1):
                w.unindent(l)
        w.endUndoAction()
    
    def createActions(self):
        self.newAct = QAction("&New", self)
        self.newAct.setShortcut("Ctrl+N")
        self.newAct.setStatusTip("Create a new file")
        self.connect(self.newAct, SIGNAL("triggered()"), self.newDoc)

        self.openAct = QAction("&Open...", self)
        self.openAct.setShortcut("Ctrl+O")
        self.openAct.setStatusTip("Open an existing file")
        self.connect(self.openAct, SIGNAL("triggered()"), self.fileOpen)
        
        self.saveAct = QAction("&Save", self)
        self.saveAct.setShortcut("Ctrl+S")
        self.saveAct.setStatusTip("Save the document to disk")
        self.connect(self.saveAct, SIGNAL("triggered()"), self.save)

        self.saveAsAct = QAction("Save &As...", self)
        self.saveAsAct.setStatusTip("Save the document under a new name")
        self.connect(self.saveAsAct, SIGNAL("triggered()"), self.saveAs)

        self.closeAct = QAction("&Close", self)
        self.closeAct.setShortcut("Ctrl+W")
        self.closeAct.setStatusTip("Close this window")
        self.connect(self.closeAct, SIGNAL("triggered()"), self.closeCurrentDoc)

        self.exitAct = QAction("E&xit", self)
        self.exitAct.setShortcut("Ctrl+Q")
        self.exitAct.setStatusTip("Exit the application")
        self.connect(self.exitAct, SIGNAL("triggered()"), qApp.closeAllWindows)
        
        self.undoAct = QAction("Undo", self)
        self.undoAct.setShortcut("Ctrl+Z")
        self.undoAct.setStatusTip("Undo")
        self.connect(self.undoAct, SIGNAL("triggered()"), self.undo)
        
        self.redoAct = QAction("Redo", self)
        self.redoAct.setShortcut("Ctrl+Shift+Z")
        self.redoAct.setStatusTip("Redo")
        self.connect(self.redoAct, SIGNAL("triggered()"), self.redo)
        
        self.cutAct = QAction("Cu&t", self)
        self.cutAct.setShortcut("Ctrl+X")
        self.cutAct.setStatusTip("Cut the current selection's contents to the clipboard")
        self.connect(self.cutAct, SIGNAL("triggered()"), self.cut)

        self.copyAct = QAction("&Copy", self)
        self.copyAct.setShortcut("Ctrl+C")
        self.copyAct.setStatusTip("Copy the current selection's contents to the clipboard")
        self.connect(self.copyAct, SIGNAL("triggered()"), self.copy)

        self.pasteAct = QAction("&Paste", self)
        self.pasteAct.setShortcut("Ctrl+V")
        self.pasteAct.setStatusTip("Paste the clipboard's contents into the current selection")
        self.connect(self.pasteAct, SIGNAL("triggered()"), self.paste)
        
        self.commentAct = QAction("&Comment", self)
        self.commentAct.setShortcut("Ctrl+E")
        self.commentAct.setStatusTip("Comment out selected lines")
        self.connect(self.commentAct, SIGNAL("triggered()"), self.comment)
        
        self.uncommentAct = QAction("&Uncomment", self)
        self.uncommentAct.setShortcut("Ctrl+Shift+E")
        self.uncommentAct.setStatusTip("Uncomment selected lines")
        self.connect(self.uncommentAct, SIGNAL("triggered()"), self.uncomment)
        
        self.unindentAct = QAction("&Unindent", self)
        self.unindentAct.setShortcut("Shift+TAB")
        self.unindentAct.setStatusTip("Unindent selected lines")
        self.connect(self.unindentAct, SIGNAL("triggered()"), self.unindent)
        
        self.findAct = QAction("&Find", self)
        self.findAct.setShortcut("Ctrl+F")
        self.findAct.setStatusTip("Find text occurence in document")
        self.connect(self.findAct, SIGNAL("triggered()"), self.find)
        
        self.findNextAct = QAction("Find next", self)
        self.findNextAct.setShortcut("F3")
        self.findNextAct.setStatusTip("Find next text occurence in document")
        self.connect(self.findNextAct, SIGNAL("triggered()"), self.findNext)

        self.syntaxCheckAct = QAction("Check syntax", self)
        self.syntaxCheckAct.setShortcut("Alt+X")
        self.syntaxCheckAct.setStatusTip("Perform syntax check")
        self.connect(self.syntaxCheckAct, SIGNAL("triggered()"), self.syntaxCheck)
        
        self.showEOLsAct = QAction("Show EOLs", self)
        #self.showEOLsAct.setShortcut("Alt+X")
        self.showEOLsAct.setStatusTip("Show end of line characters")
        self.connect(self.showEOLsAct, SIGNAL("triggered()"), self.showEOLs)
        self.showEOLsAct.setCheckable(True)
        
        self.unixLFAct = QAction("Unix LF", self)
        self.unixLFAct.setStatusTip("Change line ends to Unix LF")
        self.connect(self.unixLFAct, SIGNAL("triggered()"), self.unixLF)
        self.winCRLFAct = QAction("Windows CRLF", self)
        self.winCRLFAct.setStatusTip("Change line ends to Windows CRLF")
        self.connect(self.winCRLFAct, SIGNAL("triggered()"), self.winCRLF)
        self.macCRAct = QAction("Macintosh CR", self)
        self.macCRAct.setStatusTip("Change line ends to Macintosh CR")
        self.connect(self.macCRAct, SIGNAL("triggered()"), self.macCR)
        
        self.cutAct.setEnabled(False)
        self.copyAct.setEnabled(False)
        
        self.connect(self.tab_widget, SIGNAL("currentChanged(int)"), self.currentTabChanged)
    
    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.closeAct)
        self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.commentAct)
        self.editMenu.addAction(self.uncommentAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.findAct)
        self.editMenu.addAction(self.findNextAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.showEOLsAct)
        self.editMenu.addAction(self.unindentAct)
        
        self.toolsMenu = self.menuBar().addMenu(self.tr("&Tools"))
        self.toolsMenu.addAction(self.syntaxCheckAct)
        self.toolsMenu.addSeparator()
        self.toolsMenu.addAction(self.unixLFAct)
        self.toolsMenu.addAction(self.winCRLFAct)
        self.toolsMenu.addAction(self.macCRAct)
    
    def fileOpen(self):
        index = self.tab_widget.currentIndex()
        w = self.tab_widget.widget(index)
        default_dir = os.path.dirname(w.filename)
        
        filename = QFileDialog.getOpenFileName(self, 'Select text file to open', default_dir)
        if filename.isEmpty():
            self.statusMessage('Loading aborted', 2000)
            return
        
        filename = unicode(filename)
        self.newDoc(filename)
        self.statusMessage('Loaded document %s' % filename, 2000)
    
    def setCurrentTabLabel(self, mod):
        index = self.tab_widget.currentIndex()
        w = self.tab_widget.widget(index)
        filename = w.filename or DEFAULT_FILENAME
        
        if w.isModified():
            self.tab_widget.setTabText(index, '* ' + os.path.basename(filename))
        else:
            self.tab_widget.setTabText(index, os.path.basename(filename))
        
        self.tab_widget.setTabToolTip(index, filename)
    
    def newDoc(self, filename=None):
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab.filename == filename:
                self.tab_widget.setCurrentWidget(tab)
                return
        
        tab = QSci(self, filename)
        tab.setUtf8(True)
        
        self.connect(tab, SIGNAL('status_message'), self.statusMessage)
        self.connect(tab, SIGNAL("modificationChanged(bool)"), self.setCurrentTabLabel)
        self.connect(tab, SIGNAL("copyAvailable(bool)"), self.cutAct.setEnabled)
        self.connect(tab, SIGNAL("modificationChanged(bool)"), self.undoAct.setEnabled)
        self.connect(tab, SIGNAL("copyAvailable(bool)"), self.copyAct.setEnabled)
        
        filename = tab.filename
        
        tabname = DEFAULT_FILENAME
        if filename:
            tabname = os.path.basename(filename)
        
        if tab.isReadOnly():
            tabname = 'RO ' + tabname
        
        self.tab_widget.addTab(tab, tabname)
        self.tab_widget.setCurrentWidget(tab)
        self.tab_widget.setTabToolTip(self.tab_widget.currentIndex(), filename or 'New document')
        tab.setFocus()
        
        self.updateMenus()
    
    def updateMenus(self):
        w = self.tab_widget.currentWidget()
        
        self.undoAct.setEnabled(w.isUndoAvailable())
        self.undoAct.setEnabled(w.isRedoAvailable())
        hasSelection = w.hasSelectedText()
        self.cutAct.setEnabled(hasSelection)
        self.copyAct.setEnabled(hasSelection)
        
        self.showEOLsAct.setChecked(w.eolVisibility())
        
        self.unixLFAct.setEnabled(w.eolMode() != EOL_UNIX)
        self.winCRLFAct.setEnabled(w.eolMode() != EOL_WIN)
        self.macCRAct.setEnabled(w.eolMode() != EOL_MAC)
        
        self.syntaxCheckAct.setEnabled(w.syntaxCheckAvailable())
        
    def statusMessage(self, text, t=2000):
        self.statusBar().showMessage(text, t)
    
    def currentTabChanged(self, index):
        w = self.tab_widget.widget(index)
        if w:
            self.updateMenus()
            w.setFocus()
            self.statusMessage(w.filename or DEFAULT_FILENAME, 1000)
    
    def closeCurrentDoc(self):
        if self.tab_widget.count()==1: return
        
        w = self.tab_widget.currentWidget()
        if w.close():
            self.tab_widget.removeTab(self.tab_widget.currentIndex())
            del w
            return True
        return False
    
    def closeEvent(self, ce):
        if self.fileExit():
            ce.accept()
        ce.ignore()
    
    def fileExit(self):
        tab = self.tab_widget.currentWidget()
        while tab:
            if not tab.close():
                return False
            self.tab_widget.removeTab(self.tab_widget.currentIndex())
            del tab
            tab = self.tab_widget.currentWidget()
        
        self.writeSettings()
        
        qApp.quit()


icondata = '''\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00\x1e\x08\x06\x00\x00\x00M\n\x1c)\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00\tpHYs\x00\x00\x00\xee\x00\x00\x00\xee\x01\x06\xd6\xb24\x00\x00\x00\x19tEXtSoftware\x00www.inkscape.org\x9b\xee<\x1a\x00\x00\x05=IDATH\x89\xb5\x96[LTW\x14\x86\xff=W\xc6\xa2\xed\x08\x1d\x1d\x06\x82\xe5\xa2\x88\xb4V\xb1\n\x14\xa1\xb1\xf8Pj%&\xb4QkB\xd3V\xa3\xdc\xda*I\x1fj4\x9a46\xd6\x9aX\xa5\xd1\x04\x1b%i|05\xb1\xb5\xc6K\xda\xa8EH\xa9R\x8b\n\xf6B\x11D\x91\xfb0\\\x86\xd9s\xe6\xfc}\x98 \x8c\x830C\xcbI\xd6\xcb\xd9{\x7f\xeb;g\xad\xb3\xf7\x11$\x11\xece\x12"+J\xab]\x9b\x91\x95\x95\x16\x11\x1e\xfe\xb4\xc7\xe3\xc1\x8f\'O:\x9d\x1e\xcf\xd0\x10\xf0{\x13\xf0\x8d\x0b\xb8@R\x99\x10F2\xa0\x00 \xcc\xc0\xfa\xd7\x12\x13\xef\\?z\xd4\xe5\xea\xe8\xa0B\xd2MR^\xbfNi6S\x02\xec<x\x907\x8f\x1dsoHOo\x9e\x05l\x06\xa0\x1d\x97\x1b`\xf2\x19\xd1\xc0O_\xc7\xc5\xf5\xb9\xeb\xea\xa8\xf4\xf6\xd2\xad\xaa\x94v;eA\x01\xa5FC\tP\xeat\x94\xdd\xdd\x94$\xa5\xaa\xb2\xbe\xbc\xdc\xbd,<\xbc\x1e\xc0\xdcI\x0b\x00\x88_\x16\x1e\xfe\xc7\xdf99\xaa\xb2q#\xdd\x0b\x17Rj\xb5\x94F#eh\xa87\xf1\xe8\xc8\xcf\xa7lk\xa3lj\xa2\xcc\xcbc\xabF\xc3W\x81\x96(\xe0\xdd\xa0\x05\xc2\x807\xdeKIy\xd8[XHe\xcd\x1a\xca\x90\x10\xff\x84c\x85VKi0P\xea\xf5\x94\x9b6Qn\xdd\xca\x9dqq=\x91@q\xc0\x02Q\xc0\xee\x03\xb9\xb9v\xe5\xc1\x03\xba\xeb\xea(\xd7\xae\r,\xf9\xe88~\xdc[\x0e\x92RJ\x96o\xdb\xe6\xb0\x00oM(`\x03>?\xb6dI\x9f\xe2px\x9b\x8c\xa4T\x14\xcaU\xabF\xe03fP\x1e>LY[K\xb9}\xfbH\x1f\x8c\x8e\xfb\xf7G\x04H\xca\xc6F\xae\x04\x1e\x84\x02\x99O\x14\x98\x01\xac\xfch\xde\xbc\x0e\xa5\xb4\x94\xca\xe8\xc5$eY\x99\x17,\x04\xe5\xb9s\xbec{\xf6\xf8\x0btv\xfa\xce\xb9}\x9b\x0e\x80K\x81f\x00\xf3\xfc\x04\x00\xcc~=6\xf6\x9e\xb3\xa0\x80\xca\x91#\xbe\x8bI\xef+\x05(cb\xfc\xc7H\xca\x9c\x1c_\x81\xd2R\x9f\x12\xc8\xd4TJ\x8d\x86\xed\xeb\xd6q\x99\xd5Z\xed#\x00@\xfb\x82\xd9\xfc\xeb\xc3\xfc|*\xc5\xc5t\xa7\xa5Q\x9e?O\xe9tz\x01\x97/SZ\xad^\xf0\xea\xd5c\x0b\x9c9\xe3+\xa0\xd7Sn\xdeLYTD\x99\x9c\xec\xbdWVFI\xf2\xb7\xd3\xa7]\x06 \xf3\x91@$p\xa8\xe9\xd4)\xb7\xa2(T*+\xbd\x8b\x87;::\xda\x17\x9c\x9d=\xb6\xc0\xd9\xb3\x137\xe6p_\xb8\xddL\x8f\x89\xb93\xfc\xf4\xc9\xdf\xee\xda\xd5\xa7\x90#\xbb\x9b\xc52>\xe8\xda5\xdf\xe4CC\x94YYO\x9c\xdf\x03\xf0*\xc0\x8byy\xaeCEE]\xcbm\xb6\x1bQ\xc0\x87\x82$\xd2l\xb6\x8a+w\xef\xbe,\xf4z\x00\x80\xda\xd0\x00\xc4\xc7\x03\xe3\x9d\x13\t\t\xc0\x8e\x1d\x80\xcd\x06TU\x01\xe5\xe5@]\x1d\x00\xa0\x1d@\r\xc0\x9f\x81\xce_\x80\xc1\x1e\xa0o\x10hw\x01\xd5-@\x05\x80J\x92=\xc3\xa8\x05g\xf7\xef\xef\x1f~z\x85\xa4,)\t\xf8[\xef\x02\xf8\x83\x10\xdc\x1dff\xa6\xd1\xa0.\x00jc\x81\xd3f\xa0\x00\xc0\x8b\x00\xf4\xe3\xee\xb4s\x80#\xfd7o>J\xee>q\xc2\xbb\x8b=!\xe1 \xc0z\x80\x87\x9e\x9a\xc67\xa3\xa3\xf8vF*\x0f|\xb6\x93\x97.}\xc7\xa5K\x17\rM\xb4\xb5?\x1e:\x83\x10\xa9\x86\xeajx\\.\x0c\\\xbd\x8a\xc6\x92\x12\xd8\xddn8\x00\xd8\x01O+0x\x1b\xe8o\x02\xe4\x00\xd0\xdf\x0fh\x17\xa4,Ix\xe7\xe3b|\x95\x9e\n\xbd^\xf7\xa8*\xd3\xa7O\x87\x10\xc2D\xd2\x19\xc0\xa9\x0e\x00\xd0\xb9\xc8\xe6\xc5[\xb68TE\xb1\xab\xaa\xda\xad\x02].\xa0\xbd\x0fh\xeb\xf6\x96\xb3\x0b\xc0?$\xdb\x00 &f\xce\x97%\xfbv\'$%\xcd\xf7\x83-_\x9e\xa2\xad\xae\xbe\x96\x05\xe0\xfb@\x05\x04\x83\xfc!\x89\x8b{\xae\xb2\xaa\xeaB\xaa\xc1\xa0\xf7\x1b\xb3\xdb{\xb1bENMC\xc3\xdd\xe4@y\xba\x89\xa7\xf8]-\xeb\xd7\xbf/32\xd2\x0cCCCp8\xfa\xd0\xda\xda\x06\x8f\xc7\x83[\xb7\xea\x07T\x95\x17\x83\xa2\x05\xdb4$\x91\x98\x18_[Qq\x9255g\xd8\xd8x\x85Ng=\xfb\xfb\xfebnnv+\x00K0\xacI\t$%\xcd\xbd!\xe5\x9f\x1c\x1d\xbd\xf6\x06VW_P##g\x7f\x12\x0cK3\x89\x12\x80\x84x\xfc\x9eV\xa7"\xca\x16\'l6\xeb&!\x84!P\xd6$\x05\xe8\'\xa0\xd3\x11\xa4\xc0\x17\xfb>\x8d\x88\x8c\x9c\xfd\xc1\x94\n\x00\xfe\x02\x1a\x8d7bc\xe6\xebf\xce4\x17\n!\x8cS&`4\x1a\xc6\x84\xeb\r*H`\xef\xde\x9dV\x8b%<\x7fJ\x04\x84\x10\x1a\x93)$dL\xb1\x10\x15\x00\xb0x\xd1K\xfa\xb0\xb0g\xb6\x08!\xfc\xde\xd4\x7f\x16\x00\xf0lD\xc4,\xedX\x03z=\xa1\xd1\x00\x8a[\x83\r\x1br\xc3\x00<?\x15\x02\xce\xc1A\xa7g\xac\x01!\xbce\x00\x80\xcc\x8cT\xb3\xd5j\xc9\xfe\xdf\x05H:\x1a\x1b\xef\xb5\xb5\xb4\xb4\xc2\xe3\xf1\xf70\x99T\x0c\x0cv`\xeb\xb6\x1d\xf7\x8dFC\xfdD\xbc\xa0\xcf\x02\x00\xb0Z-\xaf\x84\x86N\xcb\x07`\x0b\t1N3\x99L!&\x93\xd1\xe8rI\xf7\xc0\x80s\xd0\xe9t6444\x17\x92|8\x11\xeb_\xd4\x8f\xe4\x00\xd4\x0cPu\x00\x00\x00\x00IEND\xaeB`\x82'''


if __name__=="__main__":
    
    app = QApplication(sys.argv)
    main_window = ApplicationWindow()
    pixmap = QPixmap()
    pixmap.loadFromData(icondata, 'PNG')
    appico = QIcon(pixmap)
    app.setWindowIcon(appico)
    
    files = sys.argv[1:]
    
    if files:
        for f in files:
            #f = os.path.expanduser(f)
            f = os.path.abspath(f)
            main_window.newDoc(f)
    else:
        main_window.newDoc()
    
    main_window.show()
    
    sys.exit(app.exec_())
