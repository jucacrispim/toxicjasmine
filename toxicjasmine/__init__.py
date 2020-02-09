# -*- coding: utf-8 -*-
# Copyright 2018 Juca Crispim <juca@poraodojuca.net>

# This file is part of jasmacs.

# jasmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# jasmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with jasmacs. If not, see <http://www.gnu.org/licenses/>.

import argparse
import mimetypes
import os
import pkg_resources
import sys
import cherrypy
from jasmine_core.core import Core
from jasmine.config import Config
from jasmine.entry_points import Command
from jasmine.standalone import JasmineApp
from jasmine.ci import CIRunner, TestServerThread


class ToxicjasmineApp(JasmineApp):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.jasmine_file = ToxicjasmineFile()


class ToxicjasmineCore(Core):

    @classmethod
    def css_package(cls):
        return __package__

    @classmethod
    def js_package(cls):
        return __package__

    @classmethod
    def css_files(cls, theme='dark'):
        css_filter = theme + '.css'

        return cls._uniq(sorted(filter(
            lambda x: css_filter in x, pkg_resources.resource_listdir(
                cls.css_package(), ''))))

    @classmethod
    def js_files(cls):
        js_files = sorted(list(filter(
            lambda x: '.js' in x, pkg_resources.resource_listdir(
                cls.js_package(), ''))))

        # jasmine.js needs to be first
        js_files.insert(0, 'jasmine.js')

        # boot needs to be last
        js_files.remove('boot.js')
        js_files.append('boot.js')

        return cls._uniq(js_files)


class ToxicjasmineConfig(Config):
    def __init__(self, *args, **kwargs):
        self.theme = kwargs.pop('theme', 'clear')
        self.browser_options = kwargs.pop('options', [])
        super().__init__(*args, **kwargs)

    def stylesheet_urls(self):

        jasmine_css = [
            "/__jasmine__/{0}".format(core_css)
            for core_css in ToxicjasmineCore.css_files(theme=self.theme)]

        src_css = [
            "/__src__/{0}".format(css_file)
            for css_file in self.stylesheets()]

        return jasmine_css + src_css

    def script_urls(self):
        core_js_files = ToxicjasmineCore.js_files()
        if 'node_boot.js' in core_js_files:
            core_js_files.remove('node_boot.js')

        jasmine_js = [
            "/__jasmine__/{0}".format(core_js) for core_js in core_js_files]

        src_js = [self._prefix_src_underscored(src_file)
                  for src_file in self.src_files()]

        helpers = ["/__spec__/{0}".format(helper) for helper in self.helpers()]

        specs = ["/__spec__/{0}".format(spec_file)
                 for spec_file in self.spec_files()]
        return jasmine_js + src_js + helpers + specs


class ToxicjasmineCommand(Command):
    """Jasmine with a new other css theme and new ci options to
    pass to the browser."""

    def __init__(self, app, ci_runner):
        self.app = app
        self.ci_runner = ci_runner
        self._args = None
        self.parser = argparse.ArgumentParser(
            description='Jasmine command line')
        subcommands = self.parser.add_subparsers(help='commands')
        server = subcommands.add_parser(
            'server', help='Jasmine server',
            description='run a server hosting your Jasmine specs')
        server.add_argument('-p', '--port', type=int, default=8888,
                            help='The port of the Jasmine html runner')
        server.add_argument('-o', '--host', type=str, default='127.0.0.1',
                            help='The host of the Jasmine html runner')
        server.add_argument('-c', '--config', type=str,
                            help='Custom path to jasmine.yml')
        server.add_argument('-r', '--root', type=str, default=None,
                            help="The root dir for the jasmine server process")
        server.set_defaults(func=self.server)

        ci = subcommands.add_parser(
            'ci', help='Jasmine CI',
            description='execute your specs in a browser')
        ci.add_argument('-b', '--browser', type=str,
                        help='The selenium driver to utilize')
        ci.add_argument('-l', '--logs', action='store_true',
                        help='Displays browser logs')
        ci.add_argument('-s', '--seed', type=str,
                        help='Seed for random spec order')
        ci.add_argument('-c', '--config', type=str,
                        help='Custom path to jasmine.yml')
        ci.add_argument('-t', '--theme', type=str, default='clear',
                        help="The theme's name for the html report")
        ci.add_argument('-i', '--options', type=str,
                        help='Browser options')

        ci.set_defaults(func=self.ci)

        init = subcommands.add_parser('init', help='initialize Jasmine',
                                      description='')
        init.set_defaults(func=self.init)

    def run(self, argv):

        args = self.parser.parse_args(argv)
        self._args = args
        if getattr(args, 'root', None):
            os.chdir(args.root)

        try:
            args.func(args)
        except AttributeError:
            self.parser.print_help()

    def _load_config(self, custom_config_path):
        config_file, project_path = self._config_paths(custom_config_path)
        return ToxicjasmineConfig(config_file, project_path=project_path,
                                  theme=self._args.theme,
                                  options=self._args.options)


class ToxicjasmineFile(object):
    @cherrypy.expose
    def index(self, path):
        if path == 'jasmine_favicon':
            return cherrypy.lib.static.serve_fileobj(
                pkg_resources.resource_stream(
                    'jasmine_core.images',
                    'jasmine_favicon.png'
                ),
                content_type='image/png'
            )
        mime_type, _ = mimetypes.guess_type(path)
        return cherrypy.lib.static.serve_fileobj(
            pkg_resources.resource_stream('toxicjasmine', path),
            content_type=mime_type
        )


class ToxicJasmineCIRunner(CIRunner):

    def _get_browser(self, browser):
        driver = browser if browser \
            else os.environ.get('JASMINE_BROWSER', 'firefox')
        options = self.jasmine_config.browser_options
        browser_opts = [o for o in options.split(',')] if options else []
        try:
            webdriver = __import__(
                "selenium.webdriver.{0}.webdriver".format(driver),
                globals(), locals(), ['object'], 0
            )
            options = webdriver.Options()
            for option in browser_opts:
                options.add_argument('--{}'.format(option))

            if driver == 'chrome':
                kw = {'chrome_options': options}
            elif driver == 'firefox':
                kw = {'firefox_options': options}
            else:
                kw = {}

            return webdriver.WebDriver(**kw)
        except ImportError:
            print("Browser {0} not found".format(driver))


def begin():

    cmd = ToxicjasmineCommand(ToxicjasmineApp, ToxicJasmineCIRunner)

    if 'python' in sys.argv or 'python3' in sys.argv:
        args = sys.argv[2:]
    else:
        args = sys.argv[1:]

    cmd.run(args)


if __name__ == '__main__':
    begin()
