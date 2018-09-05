#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

"""
Fuchsine main service
"""

import os
import time
import bottle
import pathlib
import threading

from . import __version__
from .template import *
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def get_path_type(path):
    """Determine what type of path it is"""
    if os.path.isfile(path):
        return "File"
    else:
        return "Directory"

def generate_http_response(body=None, status=None, headers=None):
    """Generate proper HTTP response"""
    headers = headers or dict()
    headers['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    headers['Server'] = "Fuchsine/" + __version__
    return bottle.HTTPResponse(body, status, **headers)

class Server(bottle.Bottle):
    def __init__(self, config):
        """Setup bottle object"""
        super(Server, self).__init__()
        self.config = config
        # Initialize index
        self.index = dict()
        self.build_index()
        # Routes
        self.route('/', callback=self.redirect_to_files)
        self.route('/files', callback=self.redirect_to_files)
        self.route('/files/', callback=self.route_files)
        self.route('/files/<file_path:path>', callback=self.route_files)
        self.route('/assets/<file_path:path>', callback=self.serve_assets)

    class FileChangeHandler(FileSystemEventHandler):
        def __init__(self, outer):
            self.upper = outer

        def on_modified(self, event):
            self.upper.build_index()

    class FileChangeListener(threading.Thread):
        def __init__(self, outer, handler):
            threading.Thread.__init__(self)
            self.outer = outer
            self.handler = handler

        def run(self):
            observer = Observer()
            observer.schedule(self.handler, path=self.outer.config['DEFAULT']['root'], recursive=True)
            observer.start()

    def build_index(self):
        print("(Re)building index...")
        new_index = dict()
        for path, subdirs, files in os.walk(self.config['DEFAULT']['root'], followlinks=True):
            for name in (files + subdirs):
                file_path = "/" + str(pathlib.PurePath(path, name) \
                    .relative_to(*pathlib.PurePath( \
                        self.config["DEFAULT"]['root']).parts[:1]))
                real_path = self.config['DEFAULT']['root'] + "/" + file_path
                new_index[file_path] = dict()
                new_index[file_path]['type'] = get_path_type(real_path)
                new_index[file_path]['mtime'] = os.path.getmtime(real_path)
                if self.config['DEFAULT']['file_size']:
                    new_index[file_path]['size'] = os.path.getsize(real_path)
        self.index = new_index
        print("Done.")
    
    def render_index(self, file_path):
        """Render indexes"""
        # Initialize response
        file_path = "/" + file_path
        source = dict()
        source['path'] = file_path
        source['config'] = self.config['DEFAULT']
        source['files'] = dict()
        for path in self.index.keys():
            if (path.startswith(file_path)) and ("/" not in path[len(file_path):]):
                source['files'][path[len(file_path):]] = self.index[path]
        # Render and return response
        return generate_http_response(body=render_page(self.config['DEFAULT']['template'] + "/index.html", source))

    def route_files(self, file_path=None):
        """Serve the files"""
        # Get real path
        file_path = file_path or ""
        real_path = self.config['DEFAULT']['root'] + "/" + str(file_path)
        # Get that kind of path it is
        path_type = get_path_type(real_path)
        if path_type == "File":
            return bottle.static_file(file_path, root=self.config['DEFAULT']['root'], download=str(file_path))
        else:
            if os.path.isdir(real_path):
                if (not file_path.endswith("/")) and (file_path != ""):
                    bottle.redirect(self.config['DEFAULT']['base_url'] + '/files/' + file_path + '/')
                return self.render_index(file_path)
            else:
                return bottle.abort(404, "File not found")
        return bottle.abort(500, "Unknown server error")

    def serve_assets(self, file_path):
        return bottle.static_file(file_path, root=self.config['DEFAULT']['template'] + "/assets")

    def redirect_to_files(self):
        """Redirect to subdirectory 'files/'"""
        bottle.redirect(self.config['DEFAULT']['base_url'] + '/files/')

    def rocknroll(self):
        handler = self.FileChangeHandler(self)
        listener = self.FileChangeListener(self, handler)
        listener.start()
        self.run(host=self.config['DEFAULT']['host'], port=self.config['DEFAULT']['port'])

def start(config):
    """Start the service"""
    server = Server(config)
    server.rocknroll()
