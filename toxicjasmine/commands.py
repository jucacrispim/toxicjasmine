# -*- coding: utf-8 -*-

import argparse
import os
import socket
import sys


from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.wait import WebDriverWait

from .console_formatter import ConsoleFormatter
from .js_api_parser import Parser
from .server import ToxicjasmineServer


class Command:

    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Toxicjasmine')
        subcommands = self.parser.add_subparsers(help='commands')
        for cls in type(self).__subclasses__():
            cls(subcommands)

    def run(self):
        args = self.parser.parse_args()
        args.fn(args)


class Serve(Command):

    def __init__(self, subcommands):
        self.parser = subcommands.add_parser(
            'serve',
            description='Runs a simple web server')
        self.parser.add_argument('root_dir',
                                 help="root directory for the server")
        self.parser.add_argument('-p', '--port', type=int, default=8000,
                                 help='Port for the server to listen on')
        self.parser.set_defaults(fn=self.run)

    def run(self, args):
        srv = ToxicjasmineServer(args.port, args.root_dir)
        srv.run()


class CI(Command):

    def __init__(self, subcommands):
        self.parser = subcommands.add_parser(
            'ci',
            description="Run the tests in a browser using selenium")
        self.parser.add_argument('fpath',
                                 help="Path for the spec runner html file")
        self.parser.add_argument('-b', '--browser', type=str,
                                 help='The selenium driver to utilize')
        self.parser.add_argument('-l', '--show-logs', action='store_true',
                                 help='Displays browser logs')
        self.parser.add_argument('-i', '--options', type=str,
                                 help='Browser options')
        self.parser.set_defaults(fn=self.run)

    def run(self, args):
        try:
            port = self._find_unused_port()
            self.browser = self._get_browser(args.browser, args.options)
            root_dir, fname = self._get_root_dir_fname(args.fpath)
            self.test_server = self._start_test_server(root_dir, port)
            url = f'http://127.0.0.1:{port}/' + fname
            self.browser.get(url)

            WebDriverWait(self.browser, 100).until(
                lambda driver:
                driver.execute_script("return jsApiReporter.finished;")
            )

            parser = Parser()
            spec_results = self._get_spec_results(parser)
            top_suite_results = self._get_top_suite_results(parser)
            suite_results = self._get_suite_results(parser) + top_suite_results
            show_logs = self._get_browser_logs(show_logs=args.show_logs)
            actual_seed = self._get_seed()

            formatter = ConsoleFormatter(
                spec_results=spec_results,
                suite_results=suite_results,
                browser_logs=show_logs,
                seed=actual_seed
            )

            str_output = formatter.format()
            _write_output(str_output)

            overall_status = self._get_overall_status()

            if overall_status == 'incomplete':
                sys.stdout.write('Incomplete: %s\n' %
                                 self._get_incomplete_reason())

            if overall_status != 'passed':
                _exit_with_error()
        finally:
            if hasattr(self, 'browser'):
                self.browser.close()
            if hasattr(self, 'test_server'):
                self.test_server.stop()

        return True

    def _find_unused_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', 0))
        addr, port = s.getsockname()
        s.close()
        return port

    def _start_test_server(self, root_dir, port):
        test_server = ToxicjasmineServer(port, root_dir)
        test_server.start()
        return test_server

    def _get_root_dir_fname(self, path):
        root_dir, fname = path.rsplit(os.path.sep, 1)
        return root_dir, fname

    def _get_browser(self, browser, browser_options):
        driver = browser if browser \
            else os.environ.get('JASMINE_BROWSER', 'firefox')

        options = browser_options
        browser_opts = [o for o in options.split(',')] if options else []

        try:
            webdriver = __import__(
                "selenium.webdriver.{0}.webdriver".format(driver),
                globals(), locals(), ['object'], 0
            )
            options = webdriver.Options()
            for option in browser_opts:
                options.add_argument('--{}'.format(option))

            kw = {'options': options}
            return webdriver.WebDriver(**kw)
        except ImportError:
            print("Browser {0} not found".format(driver))

    def _get_spec_results(self, parser):
        spec_results = []
        index = 0
        batch_size = 50
        while True:
            results = self.browser.execute_script(
                "return jsApiReporter.specResults({0}, {1})".format(
                    index,
                    batch_size
                )
            )
            spec_results.extend(results)
            index += len(results)

            if not len(results) == batch_size:
                break

        return parser.parse(spec_results)

    def _get_suite_results(self, parser):
        suite_results = []
        index = 0
        batch_size = 50
        while True:
            results = self.browser.execute_script(
                "return jsApiReporter.suiteResults({0}, {1})".format(
                    index,
                    batch_size
                )
            )

            suite_results.extend(results)
            index += len(results)

            if not len(results) == batch_size:
                break

        return parser.parse(suite_results)

    def _get_overall_status(self):
        return self.browser.execute_script(
            'return jsApiReporter.runDetails').get('overallStatus')

    def _get_incomplete_reason(self):
        return self.browser.execute_script(
            'return jsApiReporter.runDetails').get('incompleteReason')

    def _get_top_suite_results(self, parser):
        failed_expectations = self.browser.execute_script(
            "return jsApiReporter.runDetails").get('failedExpectations')

        top_suite_result = {
            "failedExpectations": failed_expectations,
            "status": "failed" if len(failed_expectations) else "passed"
        }

        return parser.parse([top_suite_result])

    def _get_seed(self):
        order = self._get_order()
        is_random = order.get('random')
        seed = order.get('seed') if is_random else None
        return seed

    def _get_order(self):
        return self.browser.execute_script(
            "return jsApiReporter.runDetails").get('order')

    def _get_browser_logs(self, show_logs):
        log = []
        if show_logs:
            try:
                log = self.browser.get_log('browser')
            except WebDriverException:
                pass
        return log


def _exit_with_error():
    sys.exit(1)


def _write_output(str_output):
    sys.stdout.write(str_output)
