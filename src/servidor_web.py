#!/usr/bin/python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
import BaseHTTPServer
import subprocess
import shlex
import datetime
import string
import importlib
import urllib
import shutil
import traceback
import threading
import SocketServer

import pypa2py
import pypa_server_config

config = pypa_server_config

# subprocess.call(args, *, stdin=None, stdout=None, stderr=None, shell=False)


MIME_TYPES = {
	'.html': 'text/html; charset=utf-8' , \
	'.htm':  'text/html; charset=utf-8' , \
	'.png':  'image/png' , \
	'.jpg':  'image/jpg' , \
	'.gif':  'image/gif' , \
	'.js' :  'application/javascript' , \
	'.css':  'text/css' , \
	'.ico':  'image/vnd.microsoft.icon' , \
	'.txt':  'text/plain' , \
	'.log':  'text/plain' ,
	'.json': 'application/json'
	}




class MyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	requests_log_file = open(config.requests_log_file, 'a')
	pypa_times = {}



	def send_response_code(self, code, message = None):
		self.response_code = code
		self.send_response(code, message)


	def do_HEAD(self):
		self.send_response_code(501)
		self.end_headers()
		self.add_request_to_log()



	def do_PUT(self):
		fichero = config.put_dir + os.path.basename(self.path)
		content_length = int(self.headers['content-length'])

		if content_length > 0 and content_length < config.max_length_put:
			fichero = open(fichero, "w")
			fichero.write( self.rfile.read(content_length) )
			fichero.close()
			self.send_response(200)
			self.end_headers()
		else:
			self.send_response(413)
			self.end_headers()

		self.add_request_to_log()



	def do_POST(self):
		page = self.file_of(self.path)
		#print 'HEADERS:', self.headers
		content_length = int(self.headers['content-length'])
		#log 'content_length', content_length

		if content_length > 0:
			if content_length < config.max_length_post:  # para no aceptar peticiones muy largas
				content = self.rfile.read(content_length)
				parameters = self.parse_parameters(content)
				#if 'content-type' in self.headers and self.headers['content-type'] = 'multipart/form-data'
				#        parameters = content
                                #else:
				#        parameters = self.parse_parameters(content)
				#print parameters
				self.execute(page, parameters, content)
		else:
			self.execute(page)



	def do_GET(self):
		file_of_path = self.file_of(self.path)

		if '?' in file_of_path:
			# tiene argumentos
			i = file_of_path.find('?')
			parameters = file_of_path[i+1:]
			file_of_path = file_of_path[:i]
			parameters = self.parse_parameters(parameters)
		else:
			parameters = {}

		self.execute(file_of_path, parameters, '')



	def _get_status (self):
		return "I'm OK. Thanks."



	def execute(self, page, parameters, content):
		#page = page.lower()

		try:
			fichero_pypa = page + '.pypa'
			fichero_pypah = fichero_pypa + 'h'

			if page == 'root/':
				self.send_response_code(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				self.wfile.write(config.HELLO)
				self.add_request_to_log()

			# miramos si existe el fichero pero terminado en .pypa
			elif os.path.exists(fichero_pypa):
				req_dir = page[ : page.rfind('/') ]
				req_file = page[page.rfind('/') + 1 : ]
				req_file = '_tmp_' + req_file.replace('.','_') + '.py'
				fichero_py = req_dir + '/' + req_file
				""" fichero dinamico """
				modulo = fichero_py.replace('/', '.')
				modulo = modulo[:-3]

				#if DEBUG_MODE:
				pt = datetime.datetime.utcfromtimestamp( int(os.path.getmtime(fichero_pypa)) )

				if modulo in self.pypa_times:
					if self.pypa_times[modulo] < pt:
						try:
							del sys.modules[modulo]
						except:
							pass
						compilar = True
					else:
						compilar = False
				else:
					compilar = True

				if compilar:
					pypa2py.pypa_2_py(fichero_pypa, fichero_py)
					self.pypa_times[modulo] = pt

				modulo = importlib.import_module(modulo)

				self.send_response_code(200)
				self.send_header('Content-Type', self.get_mimetype(page))
				self.send_header('Cache-Control', 'no-store')
				self.end_headers()
				self.headers['client-address'] = self.client_address[0]
				modulo._pypa_(self.wfile, self.path, self.headers, parameters, content)
				
				self.add_request_to_log()
				
				if compilar:
					#pass
					os.remove(fichero_py)
					os.remove(fichero_py + 'c')

			# miramos si existe el fichero .pypah
			# (en este modo le content-type puede ser diferente y se especifica en el fichero .pypah)
			# esta parte se creo para el proyecto POZI
			elif os.path.exists(fichero_pypah):
				#self.add_debug(fichero_pypah)
				req_dir = page[ : page.rfind('/') ]
				req_file = page[page.rfind('/') + 1 : ]
				req_file = '_tmp_' + req_file.replace('.','_') + '.py'
				fichero_py = req_dir + '/' + req_file
				""" fichero dinamico """
				modulo = fichero_py.replace('/', '.')
				modulo = modulo[:-3]

				pt = datetime.datetime.utcfromtimestamp( int(os.path.getmtime(fichero_pypah)) )

				if modulo in self.pypa_times:
					if self.pypa_times[modulo] < pt:
						try:
							del sys.modules[modulo]
						except:
							pass
						compilar = True
					else:
						compilar = False
				else:
					compilar = True

				if compilar:
					pypa2py.pypa_2_py(fichero_pypah, fichero_py)
					self.pypa_times[modulo] = pt

				modulo = importlib.import_module(modulo)

				self.send_response_code(200)
				#self.send_header('Content-Type', self.get_mimetype(page))
				self.send_header('Cache-Control', 'no-store')
				#self.end_headers()
				modulo._pypa_(self.wfile, self.path, self.headers, parameters, content)
				
				self.add_request_to_log()

				if compilar:
					os.remove(fichero_py)
					os.remove(fichero_py + 'c')

			# miramos si existe el fichero estatico y no se trata de un directorio
			elif os.path.exists(page) and not os.path.isdir(page):
				local_file_time = datetime.datetime.utcfromtimestamp( int(os.path.getmtime(page)) )
				enviar = True
				#self.add_debug(page)
				if 'if-modified-since' in self.headers:
					try:
						remote_file_time = self.headers['if-modified-since']
						#self.add_debug('if-modified-since: ' + remote_file_time)
						remote_file_time = datetime.datetime.strptime(remote_file_time, '%a, %d %b %Y %H:%M:%S %Z')
						if remote_file_time == local_file_time:
							self.send_response_code(304)
							#self.add_debug('304')
							self.end_headers()
							enviar = False
					except Exception as errFormatoFecha:
						self.add_debug('ERROR date format: [%s]' % errFormatoFecha)
				if enviar:
					self.send_response_code(200)
					#self.add_debug('200')
					self.send_header('Content-type', self.get_mimetype(page))
					self.send_header('Content-length', os.path.getsize(page) )
					self.send_header('Last-Modified', local_file_time.strftime('%a, %d %b %Y %H:%M:%S GMT') )
					self.end_headers()
					f = open(page)
					shutil.copyfileobj(f, self.wfile, config.copy_file_buffer_size)
					f.close()
				if 'referer' not in self.headers:
					self.add_request_to_log()
					#self.add_debug(page + self.headers)

			else:
				self.send_response_code(404)
				self.end_headers()
				self.wfile.write(config.FILE_NOT_FOUND)
				self.add_request_to_log()

		except Exception as err:
			self.send_response_code(500)
			self.send_header('Content-type', MIME_TYPES['.html'])
			self.end_headers()
			self.add_debug( 'ERROR: %s\n' % self.log_date_time_string() )
			traceback.print_exc(file=sys.stderr)

		""" solo se escriben en el log las peticiones que 
		no tienen referer y los ficheros dinamicos """
		#self.add_request_to_log()



	def version_string(self):
		return 'SunflowerSeed'


	def get_mimetype(self, reqfile):
		mimetype = reqfile[ reqfile.rfind('.') : ]

		if mimetype in MIME_TYPES:
			return MIME_TYPES[mimetype]
		else:
			return 'application/octet-stream'



	def file_of(self, path):
		""" devuelve el path en el disco duro de la pagina solicitada """
		path = path[1:] # quita la / del principio
		if path.count('/') == 0:
			path = 'root/' + path
		return path



	def parse_parameters(self, parameters):
		# los parametros llegan en la foma nombre=valor&nombre=valor&nombre=valor ...
		cp = {}
		p = parameters.split('&')
		for x in p:
			try:
				k,v = x.split('=')
				k = urllib.unquote_plus(k)
				v = urllib.unquote_plus(v)
				cp[k] = v
			except:
				pass
		return cp



	def add_debug(self, linea):
		sys.stderr.write(linea)
		sys.stderr.write('\n')
		sys.stderr.flush()



	def add_request_to_log(self):
		if self.path in config.no_log:
			return

		user_agent = self.get_user_agent()
		for x in config.clients_no_log:
			if x in user_agent:
				return

		client_address = self.client_address[0]
		for x in config.ips_no_log:
			if x in client_address:
				return
		
		if 'referer' in self.headers:
			referer = "  " + self.headers['referer']
		else:
			referer = ""

		self.requests_log_file.write('%s  %s  %-4s  %s  %s  %s%s\n' % (
			self.log_date_time_string(), client_address, self.command,
			self.response_code, self.path, user_agent, referer ) )
		self.requests_log_file.flush()



	def get_user_agent(self):
		if 'user-agent' in self.headers:
			return self.headers['user-agent']
		else:
			return '-'



	def log_message(self, format, *args):
	    pass




class ThreadingHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass




def main (args):

	HOST, PORT = "", 9876

	httpd = ThreadingHTTPServer( (HOST, PORT) , MyRequestHandler)

	#httpd = BaseHTTPServer.HTTPServer( (HOST, PORT), MyRequestHandler)

	print "Servidor HTTP/pypa escuchando en", PORT
	sys.stderr.write("Servidor HTTP/pypa escuchando en %d\n" % PORT)

	httpd.serve_forever()



if __name__ == "__main__":
	sys.exit(main(sys.argv))

