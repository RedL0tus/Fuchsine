#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

"""
Fuchsine main service
"""

import os
import time
import bottle

from enum import Enum

from . import __version__
from .template import *

# Type of a path
class PathType(Enum):
    Directory = 0
    File = 1

def get_path_type(path):
    """Determine what type of path it is"""
    if os.path.isfile(path):
        return PathType.File
    else:
        return PathType.Directory

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
        # Routes
        self.route('/', callback=self.redirect_to_files)
        self.route('/files/', callback=self.serve_files)
        self.route('/files/<file_path:path>', callback=self.serve_files)

    def serve_files(self, file_path=None):
        """Serve the files"""
        # Get real path
        file_path = file_path or ""
        real_path = self.config['DEFAULT']['root'] + "/" + str(file_path)
        # Get that kind of path it is
        path_type = get_path_type(real_path)
        if path_type == PathType.File:
            return bottle.static_file(file_path, root=self.config['DEFAULT']['root'], download=str(file_path))
        else:
            if os.path.isdir(real_path):
                # Initialize response
                source = dict()
                source['type'] = path_type
                source['files'] = os.listdir(real_path)
                # Render and return response
                return generate_http_response(body=render_page(self.config['DEFAULT']['template'] + "/index.html", source))
            else:
                return bottle.abort(404, "File not found")
        return bottle.abort(500, "Unknown server error")

    def redirect_to_files(self):
        """Redirect to subdirectory 'files/'"""
        bottle.redirect('files/')

def start(config):
    """Start the service"""
    server = Server(config)
    server.run(host=config['DEFAULT']['host'], port=config['DEFAULT']['port'])
