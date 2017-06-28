# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import mock

from collections import OrderedDict
from six import StringIO

from knack import CLI
from knack.commands import CLICommand, CLICommandsLoader
from knack.invocation import CommandInvoker
from tests.util import MockContext

class TestCLIScenarios(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MockContext()

    def test_list_value_parameter(self):
        handler_args = {}
        def handler(args):
            handler_args.update(args)

        command = CLICommand(self.mock_ctx, 'test command', handler)
        command.add_argument('hello', '--hello', nargs='+')
        command.add_argument('something', '--something')
        cmd_table = {'test command': command}
        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            self.mock_ctx.invoke('test command --hello world sir --something else'.split())
        self.assertEqual(handler_args['something'], 'else')
        self.assertEqual(handler_args['hello'][0], 'world')
        self.assertEqual(handler_args['hello'][1], 'sir')

    def test_case_insensitive_command_path(self):
        def handler(_):
            return 'PASSED'

        command = CLICommand(self.mock_ctx, 'test command', handler)
        command.add_argument('var', '--var', '-v')
        cmd_table = {'test command': command}

        def _test(cmd_line):
            with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
                ci = CommandInvoker(ctx=self.mock_ctx)
                self.mock_ctx.invocation = ci
                return ci.execute(cmd_line.split())

        # case insensitive command paths
        result = _test('TEST command --var blah')
        self.assertEqual(result.result, 'PASSED')

        result = _test('test COMMAND --var blah')
        self.assertEqual(result.result, 'PASSED')

        result = _test('test command -v blah')
        self.assertEqual(result.result, 'PASSED')

        # verify that long and short options remain case sensitive
        with mock.patch('sys.stderr', new_callable=StringIO):
            with self.assertRaises(SystemExit):
                _test('test command --vAR blah')

            with self.assertRaises(SystemExit):
                _test('test command -V blah')

    def test_cli_exapp1(self):
        def a_test_command_handler(_):
            return [{'a': 1, 'b': 1234}, {'a': 3, 'b': 4}]

        class MyCommandsLoader(CLICommandsLoader):
            def load_command_table(self, args):
                self.command_table['abc xyz'] = CLICommand(self.ctx, 'abc xyz', a_test_command_handler)
                self.command_table['abc list'] = CLICommand(self.ctx, 'abc list', a_test_command_handler)
                return OrderedDict(self.command_table)

        mycli = CLI(cli_name='exapp1', config_dir=os.path.join('~', '.exapp1'), commands_loader_cls=MyCommandsLoader)

        expected_output = """[
  {
    "a": 1,
    "b": 1234
  },
  {
    "a": 3,
    "b": 4
  }
]
"""
        mock_stdout = StringIO()
        exit_code = mycli.invoke(['abc', 'xyz'], out_file=mock_stdout)
        self.assertEqual(expected_output, mock_stdout.getvalue())
        self.assertEqual(0, exit_code)

        mock_stdout = StringIO()
        mycli.invoke(['abc', 'list'], out_file=mock_stdout)
        self.assertEqual(expected_output, mock_stdout.getvalue())
        self.assertEqual(0, exit_code)

        expected_output = """{
  "a": 1,
  "b": 1234
}
"""
        mock_stdout = StringIO()
        mycli.invoke(['abc', 'list', '--query', '[0]'], out_file=mock_stdout)
        self.assertEqual(expected_output, mock_stdout.getvalue())
        self.assertEqual(0, exit_code)

        expected_output = "1\n"
        mock_stdout = StringIO()
        mycli.invoke(['abc', 'list', '--query', '[0].a'], out_file=mock_stdout)
        self.assertEqual(expected_output, mock_stdout.getvalue())
        self.assertEqual(0, exit_code)

if __name__ == '__main__':
    unittest.main()
