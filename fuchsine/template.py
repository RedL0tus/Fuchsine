#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

from jinja2 import Template

def render_page(template_path, source):
    with open(template_path, 'r') as template_file:
        template = Template(template_file.read())
    return template.render(source=source).encode('utf-8')
