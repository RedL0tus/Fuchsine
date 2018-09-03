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
        self.route('/files/<filepath:path>', callback=self.serve_files)
        self.route('/files/', callback=self.serve_root)

    def serve_files(self, filepath):
        path_type = get_path_type(self.config['DEFAULT']['root'] + "/" + filepath)
        source = dict()
        source['type'] = path_type
        if path_type == PathType.File:
            return bottle.static_file(filepath, root=self.config['DEFAULT']['root'], download=filepath)
        else:
            if os.path.isdir(self.config['DEFAULT']['root'] + "/" + filepath):
                source['files'] = os.listdir(self.config['DEFAULT']['root'] + "/" + filepath)
            else:
                return generate_http_response(body="<html><body><p>404 Not Found</p></body></html>", status=404)
        return generate_http_response(body=render_index(self.config['DEFAULT']['template'] + "/index.html", source))

    def serve_root(self):
        source = dict()
        source['type'] = get_path_type(self.config['DEFAULT']['root'])
        if os.path.isdir(self.config['DEFAULT']['root']):
            source['files'] = os.listdir(self.config['DEFAULT']['root'])
        else:
            return generate_http_response(body="<html><body><p>404 Not Found<br />(root directory not found)</p></body></html>", status=404)
        return generate_http_response(body=render_index(self.config['DEFAULT']['template'] + "/index.html", source))

    def redirect_to_files(self):
        headers = dict()
        headers['Location'] = "files/"
        return generate_http_response(status=302, headers=headers)

def start(config):
    server = Server(config)
    server.run(host=config['DEFAULT']['host'], port=config['DEFAULT']['port'])
