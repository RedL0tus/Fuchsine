#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
Fuchsine command line helper

Sample usage:
```
$ cp example.init config.ini
$ python3 fuchsined.py -c config.ini start
```
"""

import argparse

import fuchsine.config as config_util
import fuchsine.server as server

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="Action to take")
    parser.add_argument("-c", "--config", help="Annotate config file")
    args = parser.parse_args()
    # Get config from the given arguments
    config = config_util.get_config(args.config)
    if args.action == "start":
        server.start(config)
    else:
        print("No such action")
