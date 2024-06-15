# -*- coding: utf-8 -*-

from unittest.mock import Mock
import os

from toxicjasmine import commands

from . import TEST_DATA_DIR


def test_ci_with_tests_passed():
    ci = commands.CI(Mock())
    args = Mock(fpath=os.path.join(TEST_DATA_DIR, 'SpecRunner.html'))
    args.browser = 'chrome'
    args.show_logs = False
    args.options = None
    r = ci.run(args)

    assert r is True


def test_ci_with_tests_passed_with_browser_options():
    ci = commands.CI(Mock())
    args = Mock(fpath=os.path.join(TEST_DATA_DIR, 'SpecRunner.html'))
    args.browser = 'chrome'
    args.show_logs = False
    args.options = 'no-sandbox,headless'
    r = ci.run(args)

    assert r is True


def test_ci_with_tests_error(mocker):
    mocker.patch.object(commands, '_exit_with_error', Mock())
    ci = commands.CI(Mock())
    args = Mock(fpath=os.path.join(TEST_DATA_DIR, 'SpecRunnerError.html'))
    args.browser = 'chrome'
    args.show_logs = False
    args.options = None
    ci.run(args)

    assert commands._exit_with_error.called


def test_ci_with_tests_error_with_browser_logs(mocker):
    mocker.patch.object(commands, '_exit_with_error', Mock())
    mocker.patch.object(commands, '_write_output', Mock())
    ci = commands.CI(Mock())
    args = Mock(fpath=os.path.join(TEST_DATA_DIR, 'SpecRunnerError.html'))
    args.browser = 'chrome'
    args.show_logs = True
    args.options = None
    ci.run(args)

    assert commands._exit_with_error.called
    output = commands._write_output.call_args[0][0]
    assert 'Browser Session Logs:' in output
