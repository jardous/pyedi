#!/usr/bin/python

import sys, string, os
from qt import Qt, QAction, QApplication, QFileDialog, QListView, QListViewItem, QListViewItemIterator, QMainWindow, QMessageBox, QPixmap, QPopupMenu, QPrinter, QFont, QPoint, qApp, SIGNAL, SLOT, QEvent
import qtext
from qtext import QextScintilla as qs, QSCINTILLA_VERSION_STR

documents = []
FONT_SIZE = 10
eolM = {0:'\r\n', 1:'\r', 2:'\n'}

INDENT_WIDTH = 4

class Document:
    def __init__(self, doc, filename=''):
        name = 'untitled'
        if filename!='':
            print filename
            name = os.path.basename(filename)
        
        enames = [d.name for d in documents]
        
        n = name
        i = 1
        while n in enames:
            n = name + '_' + str(i)
            i = i + 1
        name = n
        
        self.doc      = doc
        self.name     = name
        self.filename = filename
    
    def __repr__(self):
        return self.doc
    
    def __str__(self):
        return self.getName()
    
    def __cmp__(self, other):
        if self.doc == other:
            return 0
        return -1
    
    def getName(self):
        if not self.filename:
            return self.name
        return os.path.basename(self.filename)



class QSci(qtext.QextScintilla):
    def __init__(self, parent, doc=None):
        qtext.QextScintilla.__init__(self, parent)
        self.parent   = parent
        self.lex = None
        self.SendScintilla(qs.SCI_SETHSCROLLBAR)
        self.setupContextMenu()
        self.dnd = False
        
        print 'scintilla version', QSCINTILLA_VERSION_STR
        
        if doc:
            self.loadDocument(doc)
        
        self.SendScintilla(qs.SCI_ASSIGNCMDKEY, qs.SCK_TAB + (qs.SCMOD_CTRL<<16), qs.SCI_BACKTAB)
    
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
    
    def loadDocument(self, doc):
        try:
            f = open(doc.filename, 'r')
        except:
            return
        self.setText(f.read())
        f.close()
        
        self.setModified(False)
        self.setAutoLexer()
        #QListViewItem(self.parent.lv, doc.getName())
        self.parent.setCaption(doc.getName())
        #self.parent.tab.setTabLabel(self, doc.getName())
        self.parent.lv.updateFiles()
    
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
        currd = self.currentDoc()
        basename = ext = ''
        if currd.filename:
            basename, ext = os.path.splitext(currd.filename)
        
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
        for style in range(0, 14):
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
    
    def setupContextMenu(self):
        self.menuIds = {}
        
        self.menu = QPopupMenu(self)
        self.file = QPopupMenu(self.menu)
        self.menu.insertItem('&File', self.file)
        
        self.file.insertItem('&New', self.parent.newDoc, Qt.CTRL + Qt.Key_N)
        self.menuIds['Open'] = self.file.insertItem('&Open', self.parent.openFile, Qt.CTRL + Qt.Key_O)
        self.menuIds['Save'] = self.file.insertItem('&Save', self.saveRequest, Qt.CTRL + Qt.Key_S)
        self.menuIds['Save as'] = self.file.insertItem('Save &as', self.saveAs)
        
        self.file.insertSeparator()
        self.menuIds['Print'] = self.file.insertItem('&Print', self.parent.printDoc, Qt.CTRL + Qt.Key_P)
        self.file.insertSeparator()
        self.menuIds['Close'] = self.file.insertItem('&Close', self.parent.closeCurrentDoc,  Qt.CTRL + Qt.Key_W)
        self.menuIds['Quit'] = self.file.insertItem('&Quit', qApp, SLOT('closeAllWindows()'), Qt.CTRL + Qt.Key_Q)
        
        self.edit = QPopupMenu(self.menu)
        self.menu.insertItem('&Edit', self.edit)
        self.menuIds['Undo'] = self.edit.insertItem('Undo', self.undo, Qt.CTRL + Qt.Key_Z)
        self.menuIds['Redo'] = self.edit.insertItem('Redo', self.redo, Qt.CTRL + Qt.SHIFT + Qt.Key_Z)
        self.edit.insertSeparator()
        self.menuIds['Copy'] = self.edit.insertItem('Copy', self.copy, Qt.CTRL + Qt.Key_C)
        self.menuIds['Cut'] = self.edit.insertItem('Cut', self.cut, Qt.CTRL + Qt.Key_X)
        self.menuIds['Paste'] = self.edit.insertItem('Paste', self.paste, Qt.CTRL + Qt.Key_V)
        self.menuIds['Select all'] = self.edit.insertItem('Select all', self.selectAll, Qt.CTRL + Qt.Key_A)
        self.edit.insertSeparator()
        self.menuIds['Find'] = self.edit.insertItem('&Find', self.find, Qt.CTRL + Qt.Key_F)
        self.menuIds['Find next'] = self.edit.insertItem('Find next', self.findNext, Qt.Key_F3)
        self.edit.insertSeparator()
        self.menuIds['Duplicate'] = self.edit.insertItem('Duplicate line', self.lineDuplicate, Qt.CTRL + Qt.Key_D)
        self.menuIds['Comment'] = self.edit.insertItem('Comment', self.comment, Qt.CTRL + Qt.Key_E)
        self.menuIds['Uncomment'] = self.edit.insertItem('Uncomment', self.findNext, Qt.CTRL + Qt.SHIFT + Qt.Key_E)
        #self.edit.insertSeparator()
        self.menuIds['Uppercase'] = self.edit.insertItem('UPPERCASE', self.uppercase, Qt.CTRL + Qt.Key_U)
        self.menuIds['Lowercase'] = self.edit.insertItem('lowercase', self.lowercase, Qt.CTRL + Qt.SHIFT + Qt.Key_U)
        
        self.tools = QPopupMenu(self.menu)
        self.menu.insertItem('&Tools', self.tools)
        self.edit.insertSeparator()
        self._lev = lambda: self.setEolVisibility(not self.eolVisibility())
        self.menuIds['show eols'] = self.tools.insertItem('show EOLs', self._lev)
        id = self.tools.insertItem('Unix LF', self.convertEols)
        self.menu.setItemParameter(id, qs.SC_EOL_LF)
        self.menuIds['Unix'] = id
        id = self.tools.insertItem('Win CRLF', self.convertEols)
        self.menu.setItemParameter(id, qs.SC_EOL_CRLF)
        self.menuIds['Win'] = id
        id = self.tools.insertItem('MAC CR', self.convertEols)
        self.menu.setItemParameter(id, qs.SC_EOL_CR)
        self.menuIds['Mac'] = id
        self.connect(self.menu, SIGNAL('aboutToShow()'), self.handleMenu)
        self.edit.insertSeparator()
        self.menuIds['check syntax'] = self.edit.insertItem('Check syntax', self.checkSyntax, Qt.ALT + Qt.Key_X)
        
        self.menuIds['filelist'] = self.menu.insertItem('show/hide filelist', self.parent.shFilelist, Qt.ALT + Qt.Key_F)
    
    def checkSyntax(self):
        import re
        eline = None
        ecolumn = 0
        edescr = ''
        doc = self.currentDoc()
        
        if isinstance(self.lex, qtext.QextScintillaLexerPython):
            import compiler
            try:
                compiler.parse(str(self.text()))
            except Exception, detail:
                print 'detail X%sX' % detail #DEBUG
                match = re.match('^(.+) \(line (\d+)\)$', str(detail))
                if match:
                    edescr, eline = match.groups()
                    eline = int(eline)-1
        elif isinstance(self.lex, qtext.QextScintillaLexerHTML):
            from kid import compiler #TODO: check kid installed
            from cStringIO import StringIO
            t = StringIO(self.text())
            try:
                codeobject = compiler.compile(source=t)
            except Exception, detail:
                detail = str(detail).strip().split('\n')[-1]
                print 'detail X%sX' % detail #DEBUG
                match = re.match('(.+): line (\d+), column (\d+)$', detail)
                if match:
                    edescr, eline, ecolumn = match.groups()
                    eline, ecolumn = int(eline) - 1, int(ecolumn)
        else:
            self.parent.statusBar().message('Only Python and XML syntax check available', 2000)
        
        if eline != None:
            self.setSelection(eline, ecolumn, eline, self.lineLength(eline)-len(eolM[self.eolMode()]))
            self.ensureLineVisible(eline)
            self.ensureCursorVisible()
            self.parent.statusBar().message(edescr, 2000)
        else:
            self.parent.statusBar().message('Syntax ok', 2000)
    
    def convertEols(self, param):
        self.SendScintilla(qs.SCI_CONVERTEOLS, param)
        self.SendScintilla(qs.SCI_SETEOLMODE, param)
        self.setModified(True)
    
    def handleMenu(self):
#        self.menu.setItemEnabled(self.menuIds["Save"], self.isModified())
#        self.menu.setItemEnabled(self.menuIds["Undo"], self.isUndoAvailable())
#        self.menu.setItemEnabled(self.menuIds["Redo"], self.isRedoAvailable())
#        self.menu.setItemEnabled(self.menuIds["Cut"], self.hasSelectedText())
#        self.menu.setItemEnabled(self.menuIds["Copy"], self.hasSelectedText())
        self.menu.setItemChecked(self.menuIds["filelist"], self.parent.lv.isShown())
        eol = self.eolMode()
        self.menu.setItemChecked(self.menuIds["show eols"], self.eolVisibility())
        self.menu.setItemChecked(self.menuIds["Unix"], eol==qs.SC_EOL_LF)
        self.menu.setItemChecked(self.menuIds["Win"], eol==qs.SC_EOL_CRLF)
        self.menu.setItemChecked(self.menuIds["Mac"], eol==qs.SC_EOL_CR)
    
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
        text, res = QInputDialog.getText("pyedi - Find text", "Enter text or re to find",
                                QLineEdit.Normal, x)
        if res:
            if not self.findFirst(text, 1, 0, line, index):
                self.parent.statusBar().message(text + ' not found', 2000)
    
    def saveRequest(self):
        print 'scintilla - saveRequest'
        d = self.currentDoc()
        if d.filename == '':
            return self.saveAs()
        
        if self.isModified():
            self.save()
        else:
            print 'not modified'
            self.save()
    
    def save(self):
        d = self.currentDoc()
        try:
            f = open(d.filename, 'w+')
        except:
            self.parent.statusBar().message('Can not write to %s' % (d.filename), 2000)
            return
        
        f.write(self.text())
        f.close()
        
        print d.filename, ': setModified(False)'
        self.setModified(False)
        #self.parent.setCaption(self.filename)
        #self.parent.setTabLabel(self, self.getName())
        #self.parent.setCaption(self.getName())
        self.parent.statusBar().message('File %s saved' % (d.filename), 2000)
    
    def saveAs(self):
        d = self.currentDoc()
        fn = QFileDialog.getSaveFileName(d.filename, '', self)
        if not fn.isEmpty():
            d.filename = unicode(fn)
            self.save()
            self.setAutoLexer()
            self.parent.lv.updateFiles()
            return True
        else:
            self.parent.statusBar().message('Saving aborted', 2000)
            return False
    
    def close(self):
        if not self.isModified():
            return True
        
        d = self.currentDoc()
        res = QMessageBox.question(self, 'ped - save', 'The document\n\n' + d.filename +
            '\n\nhas been changed since the last save.\nDo you want to save it?',
            'Save', 'Cancel', 'Leave Anyway', 0, 1)
        
        if res == 0:
            if d.filename:
                return self.save()
            else:
                return self.saveAs()
        elif res == 1:
            return False
        
        return True
    
    def currentDoc(self):
        d = self.SendScintilla(qs.SCI_GETDOCPOINTER)
        dm = documents[documents.index(d)]
        return dm
    
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
                        self.parent.load(unicode(fn))
                    else:
                        self.parent.statusBar().message(fn + ' is not a file', 2000)
            self.dnd = False
            return True
        return False


class FileList(QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent, 'files', 
        #Qt.WType_Dialog | Qt.WStyle_Customize | Qt.WStyle_DialogBorder | Qt.WStyle_Tool)
        Qt.WStyle_Customize | Qt.WType_TopLevel | Qt.WStyle_Tool | Qt.WStyle_Title)
        #Qt.WType_Dialog)# | Qt.WStyle_Customize | Qt.WStyle_DialogBorder)
        self.parent = parent
        self.setCaption('filelist')
        #self.setColumnWidthMode(0, QListView.Manual)
        self.addColumn("x")
        self.addColumn("filename")
        self.setAllColumnsShowFocus(True)
        self.setMultiSelection(False)
        self.setSelectionMode(QListView.Single)
        self.setResizeMode(QListView.LastColumn)
        self.header().hide()
        self.resize(150, 200)
    
    def updateFiles(self):
        self.clear()
        for d in documents:
            i = QListViewItem(self, '', str(d))
            i.doc = d
        self.selectCurrentDoc()
    
    def selectCurrentDoc(self):
        currd = self.parent.tab.currentDoc()
        i = QListViewItemIterator(self)
        while i.current():
            if i.current().doc == currd:
                self.setCurrentItem(i.current())
                return
            i += 1
    
    def contentsMouseReleaseEvent(self, e):
        p = QPoint(self.contentsToViewport(e.pos()))
        item = self.itemAt(p)
        if item:
            self.parent.setCurrentDoc(item.doc)
    
    def closeEvent(self, e):
        self.hide()#e.ignore()




class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self, None, 'ped', Qt.WDestructiveClose)
        self.setCaption('ped')
        self.printer = QPrinter()
        self.tab = QSci(self, 'name')
        self.setCentralWidget(self.tab)
        self.statusBar().message('Ready', 2000)
        self.resize(800, 600)
        #self.move(100, 100)
        self.lv = FileList(self)
        
        self.fileSaveAction = QAction(self, "fileSaveAction")
        self.connect(self.fileSaveAction, SIGNAL("activated()"), self.fileSave)
    
    def fileSave(self):
        print 'ApplicationWindow - fileSave'
    
    def openFile(self):
        filename = QFileDialog.getOpenFileName(QString.null, QString.null, self)
        if filename.isEmpty():
            self.parent.statusBar().message('Loading aborted', 2000)
            return
        self.load(filename)
    
    def load(self, filename):
        filename = unicode(filename)
        d = self.tab.currentDoc()
        if d.filename:
            d = self.newDoc()
        d.filename = filename
        self.tab.loadDocument(d)
        
        self.setCurrentDoc(d)
        self.statusBar().message('Loaded document %s' % filename, 2000)
    
    def setCurrentDoc(self, doc):
        currd = self.tab.currentDoc()
        if doc == currd: return
        for d in documents:
            if d.getName() == doc.getName():
                self.tab.SendScintilla(qs.SCI_SETDOCPOINTER, 0, d.doc)
                self.setCaption(d.getName())
                self.tab.setMargins()
                self.tab.setAutoLexer()
    
    def newDoc(self):
        d = self.tab.SendScintilla(qs.SCI_CREATEDOCUMENT)
        self.tab.SendScintilla(qs.SCI_SETDOCPOINTER, 0, d)
        md = Document(d)
        documents.append(md)
        self.lv.updateFiles()
        #self.lv.selectCurrentDoc()
        return md
    
    def closeCurrentDoc(self):
        if self.tab.close():
            d = self.tab.currentDoc()
            i = documents.index(d)
            documents.remove(d)
            if len(documents):
                self.tab.SendScintilla(qs.SCI_SETDOCPOINTER, 0, documents[i-1].doc)
            else:
                self.newDoc()
            self.lv.updateFiles()
            self.lv.selectCurrentDoc()
            return True
        return False
    
    def shFilelist(self):
        if self.lv.isShown():
            self.lv.hide()
        else:
            self.lv.show()
    
    def printDoc(self):
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
        for d in documents:
            if not self.closeCurrentDoc():
                ce.ignore()
                return
        self.lv.close()
        ce.accept()


icondata = '''\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00\x1e\x08\x06\x00\x00\x00M\n\x1c)\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00\tpHYs\x00\x00\x00\xee\x00\x00\x00\xee\x01\x06\xd6\xb24\x00\x00\x00\x19tEXtSoftware\x00www.inkscape.org\x9b\xee<\x1a\x00\x00\x05=IDATH\x89\xb5\x96[LTW\x14\x86\xff=W\xc6\xa2\xed\x08\x1d\x1d\x06\x82\xe5\xa2\x88\xb4V\xb1\n\x14\xa1\xb1\xf8Pj%&\xb4QkB\xd3V\xa3\xdc\xda*I\x1fj4\x9a46\xd6\x9aX\xa5\xd1\x04\x1b%i|05\xb1\xb5\xc6K\xda\xa8EH\xa9R\x8b\n\xf6B\x11D\x91\xfb0\\\x86\xd9s\xe6\xfc}\x98 \x8c\x830C\xcbI\xd6\xcb\xd9{\x7f\xeb;g\xad\xb3\xf7\x11$\x11\xece\x12"+J\xab]\x9b\x91\x95\x95\x16\x11\x1e\xfe\xb4\xc7\xe3\xc1\x8f\'O:\x9d\x1e\xcf\xd0\x10\xf0{\x13\xf0\x8d\x0b\xb8@R\x99\x10F2\xa0\x00 \xcc\xc0\xfa\xd7\x12\x13\xef\\?z\xd4\xe5\xea\xe8\xa0B\xd2MR^\xbfNi6S\x02\xec<x\x907\x8f\x1dsoHOo\x9e\x05l\x06\xa0\x1d\x97\x1b`\xf2\x19\xd1\xc0O_\xc7\xc5\xf5\xb9\xeb\xea\xa8\xf4\xf6\xd2\xad\xaa\x94v;eA\x01\xa5FC\tP\xeat\x94\xdd\xdd\x94$\xa5\xaa\xb2\xbe\xbc\xdc\xbd,<\xbc\x1e\xc0\xdcI\x0b\x00\x88_\x16\x1e\xfe\xc7\xdf99\xaa\xb2q#\xdd\x0b\x17Rj\xb5\x94F#eh\xa87\xf1\xe8\xc8\xcf\xa7lk\xa3lj\xa2\xcc\xcbc\xabF\xc3W\x81\x96(\xe0\xdd\xa0\x05\xc2\x807\xdeKIy\xd8[XHe\xcd\x1a\xca\x90\x10\xff\x84c\x85VKi0P\xea\xf5\x94\x9b6Qn\xdd\xca\x9dqq=\x91@q\xc0\x02Q\xc0\xee\x03\xb9\xb9v\xe5\xc1\x03\xba\xeb\xea(\xd7\xae\r,\xf9\xe88~\xdc[\x0e\x92RJ\x96o\xdb\xe6\xb0\x00oM(`\x03>?\xb6dI\x9f\xe2px\x9b\x8c\xa4T\x14\xcaU\xabF\xe03fP\x1e>LY[K\xb9}\xfbH\x1f\x8c\x8e\xfb\xf7G\x04H\xca\xc6F\xae\x04\x1e\x84\x02\x99O\x14\x98\x01\xac\xfch\xde\xbc\x0e\xa5\xb4\x94\xca\xe8\xc5$eY\x99\x17,\x04\xe5\xb9s\xbec{\xf6\xf8\x0btv\xfa\xce\xb9}\x9b\x0e\x80K\x81f\x00\xf3\xfc\x04\x00\xcc~=6\xf6\x9e\xb3\xa0\x80\xca\x91#\xbe\x8bI\xef+\x05(cb\xfc\xc7H\xca\x9c\x1c_\x81\xd2R\x9f\x12\xc8\xd4TJ\x8d\x86\xed\xeb\xd6q\x99\xd5Z\xed#\x00@\xfb\x82\xd9\xfc\xeb\xc3\xfc|*\xc5\xc5t\xa7\xa5Q\x9e?O\xe9tz\x01\x97/SZ\xad^\xf0\xea\xd5c\x0b\x9c9\xe3+\xa0\xd7Sn\xdeLYTD\x99\x9c\xec\xbdWVFI\xf2\xb7\xd3\xa7]\x06 \xf3\x91@$p\xa8\xe9\xd4)\xb7\xa2(T*+\xbd\x8b\x87;::\xda\x17\x9c\x9d=\xb6\xc0\xd9\xb3\x137\xe6p_\xb8\xddL\x8f\x89\xb93\xfc\xf4\xc9\xdf\xee\xda\xd5\xa7\x90#\xbb\x9b\xc52>\xe8\xda5\xdf\xe4CC\x94YYO\x9c\xdf\x03\xf0*\xc0\x8byy\xaeCEE]\xcbm\xb6\x1bQ\xc0\x87\x82$\xd2l\xb6\x8a+w\xef\xbe,\xf4z\x00\x80\xda\xd0\x00\xc4\xc7\x03\xe3\x9d\x13\t\t\xc0\x8e\x1d\x80\xcd\x06TU\x01\xe5\xe5@]\x1d\x00\xa0\x1d@\r\xc0\x9f\x81\xce_\x80\xc1\x1e\xa0o\x10hw\x01\xd5-@\x05\x80J\x92=\xc3\xa8\x05g\xf7\xef\xef\x1f~z\x85\xa4,)\t\xf8[\xef\x02\xf8\x83\x10\xdc\x1dff\xa6\xd1\xa0.\x00jc\x81\xd3f\xa0\x00\xc0\x8b\x00\xf4\xe3\xee\xb4s\x80#\xfd7o>J\xee>q\xc2\xbb\x8b=!\xe1 \xc0z\x80\x87\x9e\x9a\xc67\xa3\xa3\xf8vF*\x0f|\xb6\x93\x97.}\xc7\xa5K\x17\rM\xb4\xb5?\x1e:\x83\x10\xa9\x86\xeajx\\.\x0c\\\xbd\x8a\xc6\x92\x12\xd8\xddn8\x00\xd8\x01O+0x\x1b\xe8o\x02\xe4\x00\xd0\xdf\x0fh\x17\xa4,Ix\xe7\xe3b|\x95\x9e\n\xbd^\xf7\xa8*\xd3\xa7O\x87\x10\xc2D\xd2\x19\xc0\xa9\x0e\x00\xd0\xb9\xc8\xe6\xc5[\xb68TE\xb1\xab\xaa\xda\xad\x02].\xa0\xbd\x0fh\xeb\xf6\x96\xb3\x0b\xc0?$\xdb\x00 &f\xce\x97%\xfbv\'$%\xcd\xf7\x83-_\x9e\xa2\xad\xae\xbe\x96\x05\xe0\xfb@\x05\x04\x83\xfc!\x89\x8b{\xae\xb2\xaa\xeaB\xaa\xc1\xa0\xf7\x1b\xb3\xdb{\xb1bENMC\xc3\xdd\xe4@y\xba\x89\xa7\xf8]-\xeb\xd7\xbf/32\xd2\x0cCCCp8\xfa\xd0\xda\xda\x06\x8f\xc7\x83[\xb7\xea\x07T\x95\x17\x83\xa2\x05\xdb4$\x91\x98\x18_[Qq\x9255g\xd8\xd8x\x85Ng=\xfb\xfb\xfebnnv+\x00K0\xacI\t$%\xcd\xbd!\xe5\x9f\x1c\x1d\xbd\xf6\x06VW_P##g\x7f\x12\x0cK3\x89\x12\x80\x84x\xfc\x9eV\xa7"\xca\x16\'l6\xeb&!\x84!P\xd6$\x05\xe8\'\xa0\xd3\x11\xa4\xc0\x17\xfb>\x8d\x88\x8c\x9c\xfd\xc1\x94\n\x00\xfe\x02\x1a\x8d7bc\xe6\xebf\xce4\x17\n!\x8cS&`4\x1a\xc6\x84\xeb\r*H`\xef\xde\x9dV\x8b%<\x7fJ\x04\x84\x10\x1a\x93)$dL\xb1\x10\x15\x00\xb0x\xd1K\xfa\xb0\xb0g\xb6\x08!\xfc\xde\xd4\x7f\x16\x00\xf0lD\xc4,\xedX\x03z=\xa1\xd1\x00\x8a[\x83\r\x1br\xc3\x00<?\x15\x02\xce\xc1A\xa7g\xac\x01!\xbce\x00\x80\xcc\x8cT\xb3\xd5j\xc9\xfe\xdf\x05H:\x1a\x1b\xef\xb5\xb5\xb4\xb4\xc2\xe3\xf1\xf70\x99T\x0c\x0cv`\xeb\xb6\x1d\xf7\x8dFC\xfdD\xbc\xa0\xcf\x02\x00\xb0Z-\xaf\x84\x86N\xcb\x07`\x0b\t1N3\x99L!&\x93\xd1\xe8rI\xf7\xc0\x80s\xd0\xe9t6444\x17\x92|8\x11\xeb_\xd4\x8f\xe4\x00\xd4\x0cPu\x00\x00\x00\x00IEND\xaeB`\x82'''

class pedApp(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.mw = ApplicationWindow()
        appico = QPixmap()
        appico.loadFromData(icondata, 'PNG')
        self.mw.setIcon(appico)
        
        self.files = sys.argv[1:]
    
    def start(self):
        self.mw.show()
        self.mw.lv.show()
        
        if self.files:
            for f in self.files:
                d = self.mw.newDoc()
                d.filename = f
                self.mw.tab.loadDocument(d)
        else:
            d = self.mw.newDoc()
        
        self.mw.lv.selectCurrentDoc()
        self.connect(self, SIGNAL('lastWindowClosed()'), self, SLOT('quit()'))
        self.exec_loop()



if __name__=="__main__":
    a = pedApp(sys.argv)
    a.start()
    