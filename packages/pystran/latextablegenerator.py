# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 09:52:11 2012

@author: Chris Burns
minor adaptations by stvhoey

Table.py

A module/class for creating LaTeX deluxetable's.  In a nutshell, you create
a table instance, add columns, set options, then call the pring method.'''
"""

import numpy
import os,string,re,sys
import types

FloatType = float

float_types = [FloatType, numpy.float16, numpy.float32, numpy.float64]

'''
This module provides function for working with significant
figures.
'''

epat = re.compile(r'^([^e]+)e(.+)$')

def round_sig(x, n):
   '''round floating point x to n significant figures'''
   if type(n) is not types.IntType:
      raise TypeError("n must be an integer")
   try:
      x = float(x)
   except:
      raise TypeError("x must be a floating point object")
   form = "%0." + str(n-1) + "e"
   st = form % x
   num,expo = epat.findall(st)[0]
   expo = int(expo)
   fs = string.split(num,'.')
   if len(fs) < 2:
      fs = [fs[0],""]
   if expo == 0:
      return num
   elif expo > 0:
      if len(fs[1]) < expo:
         fs[1] += "0"*(expo-len(fs[1]))
      st = fs[0]+fs[1][0:expo]
      if len(fs[1][expo:]) > 0:
         st += '.'+fs[1][expo:]
      return st
   else:
      expo = -expo
      if fs[0][0] == '-':
         fs[0] = fs[0][1:]
         sign = "-"
      else:
         sign = ""
      return sign+"0."+"0"*(expo-1)+fs[0]+fs[1]
      
def round_sig_error(x, ex, n, paren=False):
   '''Find ex rounded to n sig-figs and make the floating point x
   match the number of decimals.  If [paren], the string is
   returned as quantity(error) format'''
   stex = round_sig(ex,n)
   if stex.find('.') < 0:
      extra_zeros = len(stex) - n
      sigfigs = len(str(int(x))) - extra_zeros
      stx = round_sig(x,sigfigs)
   else:
      num_after_dec = len(string.split(stex,'.')[1])
      stx = ("%%.%df" % num_after_dec) % (x)
   if paren:
      if stex.find('.') >= 0:
         stex = stex[stex.find('.')+1:]
      return "%s(%s)" % (stx,stex)
   return stx,stex

def format_table(cols, errors, n, labels=None, headers=None, latex=False):
   '''Format a table such that the errors have n significant
   figures.  [cols] and [errors] should be a list of 1D arrays
   that correspond to data and errors in columns.  [n] is the number of
   significant figures to keep in the errors.  [labels] is an optional
   column of strings that will be in the first column.  [headers] is
   an optional list of column headers.  If [latex] is true, format
   the table so that it can be included in a LaTeX table '''
   if len(cols) != len(errors):
      raise ValueError("Error:  cols and errors must have same length")

   ncols = len(cols)
   nrows = len(cols[0])

   if headers is not None:
      if labels is not None:
         if len(headers) == ncols:
            headers = [""] + headers
         elif len(headers) == ncols+1:
            pass
         else:
            raise ValueError("length of headers should be %d" % (ncols+1))
      else:
         if len(headers) != ncols:
            raise ValueError("length of headers should be %d" % (ncols))

   if labels is not None:
      if len(labels) != nrows:
         raise ValueError("length of labels should be %d" % (nrows))

   strcols = []
   for col,error in zip(cols,errors):
      strcols.append([])
      strcols.append([])
      for i in range(nrows):
         val,err = round_sig_error(col[i], error[i], n)
         strcols[-2].append(val)
         strcols[-1].append(err)

   lengths = [max([len(item) for item in strcol]) for strcol in strcols]
   format = ""
   if labels is not None:
      format += "%%%ds " % (max(map(len, labels)))
      if latex:
         format += "& "
   for length in lengths: 
      format += "%%%ds " % (length)
      if latex:
         format += "& "
   if latex:
      format = format[:-2] + " \\\\"
   output = []
   if headers:
      if labels:
         hs = [headers[0]]
         for head in headers[1:]:
            hs.append(head)
            hs.append('+/-')
      else:
         hs = []
         for head in headers:
            hs.append(head)
            hs.append('+/-')
      output.append(format % tuple(hs))
   for i in range(nrows):
      if labels is not None:
         output.append(format % tuple([labels[i]] + [strcol[i] for strcol in strcols]))
      else:
         output.append(format % tuple([strcol[i] for strcol in strcols]))
   return output

def round_sig_error2(x, ex1, ex2, n):
   '''Find min(ex1,ex2) rounded to n sig-figs and make the floating point x
   and max(ex,ex2) match the number of decimals.'''
   minerr = min(ex1,ex2)
   minstex = round_sig(minerr,n)
   if minstex.find('.') < 0:
      extra_zeros = len(minstex) - n
      sigfigs = len(str(int(x))) - extra_zeros
      stx = round_sig(x,sigfigs)
      maxstex = round_sig(max(ex1,ex2),sigfigs)
   else:
      num_after_dec = len(string.split(minstex,'.')[1])
      stx = ("%%.%df" % num_after_dec) % (x)
      maxstex = ("%%.%df" % num_after_dec) % (max(ex1,ex2))
   if ex1 < ex2:
      return stx,minstex,maxstex
   else:
      return stx,maxstex,minstex

class Table:

   def __init__(self, numcols, justs=None, fontsize=None, rotate=False, 
         tablewidth=None, tablenum=None, caption=None, label=None):
      """
      
      Example
      ---------
      import Table
      fout = open('mytable.tex','w')
      t = Table(3, justs='lrc', caption='Awesome results', label="tab:label")
      t.add_header_row(['obj', 'X', '$\beta$'])
      col1 = ['obj1','obj2','obj3']
      col2 = [0.001,0.556,10.56]   # just numbers
      col3 = [[0.12345,0.1],[0.12345,0.01],[0.12345,0.001]]
      t.add_data([col1,col2,col3], sigfigs=2) #,col3
      t.print_table(fout)
      fout.close()
      """

      self.numcols = numcols
      self.justs = justs
      if self.justs is None:
         self.justs = ['c' for i in range(numcols)]
      else:
         self.justs = list(justs)
         if len(self.justs) != numcols:
            raise ValueError("Error, justs must have %d elements" % (numcols))
      for just in self.justs:
         if just not in ['c','r','l']:
            raise ValueError("Error, invalid character for just: %s" % just)
      self.fontsize = fontsize
      self.rotate = rotate
      self.tablewidth = tablewidth
      self.tablenum = None
      self.caption = caption
      self.label = label
      self.col_justs = []
      self.headers = []
      self.header_ids = []
      # self.data is a list of data.  Each element of the list corresponds
      #  to a separate "secton" of the table, headed by self.data_labels
      # Each element of data should be a list of self.numcols items.
      self.data = []
      self.data_labels = []
      self.data_label_types = []
      self.sigfigs = []
      self.nrows = []

   def add_header_row(self, headers, cols=None):
      '''Add a header row to the table.  [headers] should be a list of the
      strings that will be in the header.  [cols], if specified, should be a 
      list of column indexes.  If [cols] is None, it is assummed the headers
      are in order and there are no multicolumns.  If cols is specified, you
      can indicate the the ith header spans several columns by setting the
      ith value of cols to a 2-tuple of first and last columns for the span.'''
      
      if cols is None:
         if len(headers) != self.numcols:
            raise ValueError("Error, headers must be a list of length %d" %\
                  self.numcols)
         self.headers.append(headers)
         self.header_ids.append(range(self.numcols))
      else:
         ids = []
         for item in cols:
            if type(item) is types.IntType:
               ids.append(item)
            elif type(item) is types.TupleType:
               ids += range(item[0],item[1]+1)

         ids.sort
         if ids != range(self.numcols):
            raise ValueError("Error, missing columns in cols")
         self.headers.append(headers)
         self.header_ids.append(cols)
      return
   
   def add_data(self, data, label="", sigfigs=2, labeltype='cutin'):
      '''Add a matrix of data.  [data] should be a list with length equal to
      the number of columns of the table.  Each item of [data] should be a 
      list or numpy array.  A list of strings will be inserved as is.  If
      a column is a 1-D array of float type, the number of significant
      figures will be set to [sigfigs].  If a column is 2D with shape
      (N,2), it is treated as a value with uncertainty and the uncertainty
      will be rounded to [sigfigs] and value will be rounded accordingly, 
      and both will be printed with parenthetical errors.  If a label is
      given, it will be printed in the table with \cutinhead if labeltype
      is 'cutin' or \sidehead if labeltype is 'side'.'''

      if type(data) is not types.ListType:
         raise ValueError("data should be a list")
      if len(data) != self.numcols:
         raise ValueError(\
               "Error, length of data mush match number of table columns")

      for datum in data:
         if type(datum) not in [types.ListType, numpy.ndarray]:
            raise ValueError("data must be list of lists and numpy arrays")
         if len(numpy.shape(datum)) not in [1,2]:
            raise ValueError("data items must be 1D or 2D")

      nrows = numpy.shape(data[0])[0]
      for datum in data[1:]:
         if numpy.shape(datum)[0] != nrows:
            raise ValueError("each data item must have same first dimension")
      self.nrows.append(nrows)
      if len(numpy.shape(sigfigs)) == 0:
         self.sigfigs.append([sigfigs for i in range(self.numcols)])
      else:
         if len(numpy.shape(sigfigs)) != 1:
            raise ValueError("sigfigs must be scalar or have same length as number of columns")
         self.sigfigs.append(sigfigs)
      self.data_labels.append(label)
      self.data_label_types.append(labeltype)
      self.data.append(data)

   def print_table(self, fp=None):
      if fp is None:
         fp = sys.stdout
      elif type(fp) is type(""):
         fp = open(fp, 'w')
         we_open = True
      else:
         we_open = False

      self.print_preamble(fp)
      self.print_header(fp)
      self.print_data(fp)
      self.print_footer(fp)
      if we_open:
         fp.close()

   def print_preamble(self, fp):
      cols = "".join(self.justs)
      fp.write("\\begin{table}{%s}\n" % cols)
      if self.fontsize: fp.write("\\tabletypesize{%s}\n" % str(self.fontsize))
      if self.rotate: fp.write("\\rotate\n")
      if self.tablewidth is not None: 
         fp.write("\\tablewidth{%s}\n" % str(self.tablewidth))
      else:
         fp.write("\\tablewidth{0pc}\n")
      if self.tablenum:  fp.write("\\tablenum{%s}\n" % str(self.tablenum))
      fp.write("\\tablecolumns{%d}\n" % self.numcols)
      if self.caption:  
         if self.label:
            lab = "\\label{%s}" % (self.label)
            fp.write("\\caption{%s}\n" % (str(self.caption)+lab))

   def print_header(self,fp):
      fp.write("\\tablehead{\n")

      for i,headers in enumerate(self.headers):
         end = ['\\\\\n',''][i == len(self.headers)-1]
         for j,header in enumerate(headers):
            sep = [end,'&'][j < len(headers)-1]
            if len(numpy.shape(self.header_ids[i][j])) == 1:
               length = self.header_ids[i][j][1] - self.header_ids[i][j][0] + 1
               fp.write("\\multicolumn{%d}{c}{%s} %s " % (length, header,sep))
            else:
#               fp.write("\\colhead{%s} %s " % (header,sep)) #!ENKEL VOOR STIJNS PHD
               fp.write("%s %s " % (header,sep))  #!ENKEL VOOR STIJNS PHD
      fp.write("}\n")

   def print_data(self,fp):
      fp.write("\\startdata\n")

      for i,data in enumerate(self.data):
         if self.data_labels[i] != '':
            if self.data_label_types == "cutin":
               fp.write("\\cutinhead{%s}\n" % self.data_labels[i])
            else:
               fp.write("\\sidehead{%s}\n" % self.data_labels[i])

         rows = []
         for j in range(numpy.shape(data[0])[0]):
            rows.append([])
            for k in range(len(data)):
               sf = self.sigfigs[i][k]
               if len(numpy.shape(data[k])) == 1:
                  if type(data[k][j]) in float_types:
                     if numpy.isnan(data[k][j]):
                        rows[-1].append('\\ldots')
                     else:
                        rows[-1].append(round_sig(data[k][j], sf))
                  else:
                     rows[-1].append(str(data[k][j]))
               else:
#                  if numpy.isnan(data[k][j,0]):
#                     val = "\\ldots"
#                  else:
#                     val = round_sig_error(data[k][j,0],data[k][j,1],sf,
#                            paren=True)
#                  rows[-1].append(val)
                  if numpy.isnan(data[k][j][0]):
                     val = "\\ldots"
                  else:
                     val = round_sig_error(data[k][j][0],data[k][j][1],sf,
                            paren=True)
                  rows[-1].append(val)

         for row in rows:
            fp.write(" & ".join(row))
            fp.write("\\\\\n")
      
      fp.write("\\enddata\n")

   def print_footer(self, fp):
      fp.write("\\end{table}\n")