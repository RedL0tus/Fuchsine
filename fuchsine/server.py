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

def get_path_type(path):
    """Determine what type of path it is"""
    if os.path.isfile(path):
        return "File"
    else:
        return "Directory"

def generate_file_dict(path):
    """Generate a dictionary of files and directories in the given path"""
    file_dict = dict()
    orig_list = os.listdir(path)
    for item in orig_list:
        file_dict[item] = dict()
        file_dict[item]['type'] = get_path_type(str(path) + str(item))
        file_dict[item]['mtime'] = os.path.getmtime(str(path) + str(item))
    return file_dict

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
        self.route('/files', callback=self.redirect_to_files)
        self.route('/files/', callback=self.route_files)
        self.route('/files/<file_path:path>', callback=self.route_files)
        self.route('/assets/<file_path:path>', callback=self.serve_assets)
    
    def render_index(self, file_path, path_type, real_path):
        """Render indexes"""
        # Initialize response
        source = dict()
        source['path'] = file_path
        source['base_url'] = self.config['DEFAULT']['base_url'] or str(self.config['DEFAULT']['host'] + self.config['DEFAULT']['port'])
        source['type'] = path_type
        source['files'] = generate_file_dict(real_path)
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
                return self.render_index(file_path, path_type, real_path)
            else:
                return bottle.abort(404, "File not found")
        return bottle.abort(500, "Unknown server error")

    def serve_assets(self, file_path):
        return bottle.static_file(file_path, root=self.config['DEFAULT']['template'] + "/assets")

    def redirect_to_files(self):
        """Redirect to subdirectory 'files/'"""
        bottle.redirect(self.config['DEFAULT']['base_url'] + '/files/')

def start(config):
    """Start the service"""
    server = Server(config)
    server.run(host=config['DEFAULT']['host'], port=config['DEFAULT']['port'])
