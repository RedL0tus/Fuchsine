#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import configparser

def get_config_path(path):
    if path == None:
        return "config.ini"
    else:
        return path

def parse_config(path):
    config = configparser.ConfigParser()
    config.read(path)
    return config

def get_config(path):
    config = parse_config(get_config_path(path))
    return config
