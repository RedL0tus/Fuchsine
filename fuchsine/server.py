#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import os
import time
import bottle

from enum import Enum

from . import __version__
from .template import *

class PathType(Enum):
    Directory = 0
    File = 1

def get_path_type(path):
    if os.path.isfile(path):
        return PathType.File
    else:
        return PathType.Directory

def generate_http_response(body=None, status=None, headers=None):
    headers = headers or dict()
    headers['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    headers['Server'] = "Fuchsine/" + __version__
    return bottle.HTTPResponse(body, status, **headers)

class Server(bottle.Bottle):
    def __init__(self, config):
        super(Server, self).__init__()
        self.config = config
        self.route('/', callback=self.redirect_to_files)
        self.route('/files/', callback=self.serve_files)
        self.route('/files/<file_path:path>', callback=self.serve_files)

    def serve_files(self, file_path=None):
        file_path = file_path or ""
        real_path = self.config['DEFAULT']['root'] + "/" + str(file_path)
        path_type = get_path_type(real_path)
        source = dict()
        source['type'] = path_type
        if path_type == PathType.File:
            return bottle.static_file(file_path, root=self.config['DEFAULT']['root'], download=str(file_path))
        else:
            if os.path.isdir(real_path):
                source['files'] = os.listdir(real_path)
            else:
                return bottle.abort(404, "File not found")
        return generate_http_response(body=render_page(self.config['DEFAULT']['template'] + "/index.html", source))

    def redirect_to_files(self):
        bottle.redirect('files/')

def start(config):
    server = Server(config)
    server.run(host=config['DEFAULT']['host'], port=config['DEFAULT']['port'])
