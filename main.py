#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import argparse

import fuchsine.server as server
import fuchsine.config as config_util

if __name__ == '__main__':
    #server.start()
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="Action to take")
    parser.add_argument("-c", "--config", help="Annotate config file")
    args = parser.parse_args()
    config = config_util.get_config(args.config)
    if args.action == "start":
        server.start(config)
