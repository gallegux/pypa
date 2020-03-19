"""
restricciones al codigo de un fichero .pypa

<% debe ir solo en una linea y al principio
%> debe ir solo en una linea, importa la tabulacion

"""

import sys, os


def pypa_2_py(fichero_pypa, fichero_py):

	fichero_pypa = open(fichero_pypa, 'r')
	pypa = fichero_pypa.read()
	lineas = pypa.split('\n')

	# p: linea python ; h: linea html
	tipo = 'h'

	for x in range(len(lineas)):
		ls = lineas[x].strip()

		# procesamos codigo de python
		if tipo == 'p':
			if not lineas[x-1].strip().endswith('\\'):
				# si la linea anterior no termino en \ anadimos una tabulacion
				lineas[x] = '\t' + lineas[x]
				if ls.startswith('print '):
					lineas[x] = lineas[x].replace('print ', '_write_(', 1).rstrip() + ')'
					#lineas[x] = lineas[x] + ')'
				if ls.startswith('log '):
					lineas[x] = lineas[x].replace('log ', '_log_(', 1).rstrip() + ')'
					#lineas[x] = lineas[x] + ')'

		# procesamos las marcas de pypa
		if ls == '<%':
			tipo = 'p'

		if ls.endswith('%>'):
			tipo = 'h'


	pypa = '\n'.join(lineas)
	lineas = None

	pypa = pypa.replace('<%', '\"\"\")')
	#pypa = pypa.replace('%>\r\n', 'out.write(\"\"\"')
	#pypa = pypa.replace('%>\n', 'out.write(\"\"\"')
	#pypa = pypa.replace('%>', 'out.write(\"\"\"')
	pypa = pypa.replace('%>\r\n', '_write_(\"\"\"')
	pypa = pypa.replace('%>\n', '_write_(\"\"\"')
	pypa = pypa.replace('%>', '_write_(\"\"\"')

	#pypa = pypa.replace('<?', '\"\"\" + str(')
	pypa = pypa.replace('<?', '\"\"\", str(')
	#pypa = pypa.replace('?>', ') + \"\"\"')
	pypa = pypa.replace('?>', '), \"\"\"')

	pypa = pypa.replace( 'out.write(\"\"\"\"\"\")' , '' )






	
	

	pypa = """#!/usr/bin/python
# -*- coding: utf-8 -*-


import os, sys


def _pypa_(out, request_url, headers = {}, parameters = {}, _content = ''):



	def _write_(*items):
		for x in items:
			out.write(str(x))

			
	def _log_(*items):
		c = 0
		for x in items:
			if c > 0:
				sys.stderr.write(' ')
			c = c + 1
			sys.stderr.write( str(x) )
		sys.stderr.write('\\n')
		sys.stderr.flush()



	out.write(\"\"\"""" + pypa + """\"\"\")
"""

	fichero_py = open(fichero_py, 'w')
	fichero_py.write(pypa)

	fichero_pypa.close()
	fichero_py.close()

