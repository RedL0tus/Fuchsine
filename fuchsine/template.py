#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

"""
Fuchsine template processing utility

Currently it uses Jinja2 as template engine
"""

from jinja2 import Template

def render_page(template_path, source):
    """Render the page"""
    # Read template from given path
    with open(template_path, 'r') as template_file:
        template = Template(template_file.read())
    # Return rendered file
    return template.render(source=source).encode('utf-8')
