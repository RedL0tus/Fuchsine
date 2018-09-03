#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

"""
Fuchsine configuration utility

Find config file and parse it using configparser
"""

import configparser

def get_config_path(path):
    """Process the given path to configuration file"""
    if path == None:
        # If no path is given, return default path
        return "config.ini"
    else:
        return path

def parse_config(path):
    """Read and parse the configuration file"""
    config = configparser.ConfigParser()
    config.read(path)
    return config

def get_config(path):
    """All-in-one wrapper"""
    config = parse_config(get_config_path(path))
    return config
