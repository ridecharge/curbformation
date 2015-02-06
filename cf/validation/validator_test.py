#!/usr/bin/env python3
import unittest
from cf.validation.validator import NestedStackValidator
from unittest.mock import MagicMock
from boto.exception import BotoServerError
from unittest.mock import patch
import json


def do_pass(_):
    pass


@patch('time.sleep', do_pass)
class NestedStackValidatorTest(unittest.TestCase):
    def setUp(self):
        self.cf_conn = MagicMock()
        self.cf_conn.validate_template = MagicMock(return_value=True)
        self.validator = NestedStackValidator(self.cf_conn, './')
        with open('test.json') as file:
            self.data = json.load(file)
        with open('test_bad.json') as bad_file:
            self.bad_data = json.load(bad_file)
        self.stack = MagicMock()
        self.stack.template_body = self.data

    def test_return_false_when_invalid_syntax(self):
        self.cf_conn.validate_template = MagicMock(side_effect=BotoServerError('failed', 'failed'))
        self.assertFalse(self.validator.validate(self.stack))

    def test_return_true_when_valid(self):
        self.assertTrue(self.validator.validate(self.stack))

    def test_return_false_when_nested_validation_fails(self):
        self.stack.template_body = self.bad_data
        self.assertFalse(self.validator.validate(self.stack))


if __name__ == '__main__':
    unittest.main()
