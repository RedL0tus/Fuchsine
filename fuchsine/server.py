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
    """Fuchsine server main object (Bottle)"""

    def __init__(self, config):
        """Setup server"""
        super(Server, self).__init__()
        # Save config
        self.config = config
        # Initialize index
        self.index = dict()
        self.build_index()
        # Routes
        self.route('/', callback=self.main_router)
        self.route('/<file_path:path>', callback=self.main_router)

    class FileChangeHandler(FileSystemEventHandler):
        """Just like its name"""
        def __init__(self, outer):
            # Pass outer object inside
            self.upper = outer

        def on_modified(self, event):
            """
            Regenerate index when there are any modification in the watching directory
            """
            self.upper.build_index()

    class FileChangeListener(threading.Thread):
        """Second thread that listen to file system change"""
        def __init__(self, outer, handler):
            threading.Thread.__init__(self)
            # Pass outer object and handler inside
            self.outer = outer
            self.handler = handler

        def run(self):
            # Start watchdog
            observer = Observer()
            observer.schedule(self.handler, path=self.outer.config['DEFAULT']['root'], recursive=True)
            observer.start()

    def build_index(self):
        """Build file index"""
        print("(Re)building index...")
        # Create new dict, avoid overwriting existing index
        new_index = dict()
        # Iterate through all files and directories in the annotated directory
        for path, subdirs, files in os.walk(self.config['DEFAULT']['root'], followlinks=True):
            for name in (files + subdirs):
                # Get relative path
                file_path = "/" + str(pathlib.PurePath(path, name) \
                    .relative_to(pathlib.PurePath( \
                        self.config["DEFAULT"]['root'])))
                # Get real path
                real_path = self.config['DEFAULT']['root'] + file_path
                # Catch frequent errors
                try:
                    # Gather information needed
                    new_index[file_path] = dict()
                    new_index[file_path]['type'] = get_path_type(real_path)
                    new_index[file_path]['mtime'] = os.path.getmtime(real_path)
                    if self.config['DEFAULT']['file_size']:
                        new_index[file_path]['size'] = os.path.getsize(real_path)
                except FileNotFoundError:
                    print("Found one missing file: " + real_path)
                except OSError:
                    print("Error while creating index for: " + real_path)
        # Replace index
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
        path_found = False
        for path in self.index.keys():
            if (path + "/").startswith(file_path):
                path_found = True
                if path.startswith(file_path) and ("/" not in path[len(file_path):]):
                    source['files'][path[len(file_path):]] = self.index[path]
        if path_found:
            # Render and return response
            return generate_http_response(body=render_page(self.config['DEFAULT']['template'] + "/index.html", source))
        else:
            return bottle.abort(404, "Path not found")

    def serve_assets(self, file_path):
        """Serve template files"""
        return bottle.static_file(file_path, root=self.config['DEFAULT']['template'])

    def main_router(self, file_path=None):
        """Main router"""
        file_path = file_path or ""
        # Resource file routing
        # TODO: Make this route customizable
        if file_path.startswith("fuchsine/"):
            return self.serve_assets(file_path[9:])
        # Get real path
        real_path = self.config['DEFAULT']['root'] + "/" + str(file_path)
        # Get that kind of path it is
        path_type = get_path_type(real_path)
        if path_type == "File":
            # Direct serve the files
            return bottle.static_file(file_path, root=self.config['DEFAULT']['root'], download=str(file_path))
        else:
            if (not file_path.endswith("/")) and (file_path != ""):
                bottle.redirect(self.config['DEFAULT']['base_url'] + '/' + file_path + '/')
            return self.render_index(file_path)
        return bottle.abort(500, "Unknown server error")

    def rocknroll(self):
        handler = self.FileChangeHandler(self)
        listener = self.FileChangeListener(self, handler)
        listener.start()
        self.run(host=self.config['DEFAULT']['host'], port=self.config['DEFAULT']['port'])

def start(config):
    """Start the service"""
    server = Server(config)
    server.rocknroll()
