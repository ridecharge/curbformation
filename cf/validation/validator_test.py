#!/usr/bin/env python3
import unittest
from cf.validation.validator import NestedStackValidator
from unittest.mock import MagicMock
from boto.exception import BotoServerError
from unittest.mock import patch


def do_pass(var):
    return var


@patch('time.sleep', do_pass)
class NestedStackValidatorTest(unittest.TestCase):
    def setUp(self):
        self.cf_conn = MagicMock()
        self.cf_conn.validate_template = MagicMock(return_value=True)
        self.template_path = 'test.json'
        self.validator = NestedStackValidator(self.cf_conn, self.template_path)

    def test_return_false_when_invalid_syntax(self):
        self.cf_conn.validate_template = MagicMock(side_effect=BotoServerError('failed', 'failed'))
        self.validator.validate()
        self.assertFalse(self.validator.validate())

    def test_return_true_when_valid(self):
        self.assertTrue(self.validator.validate())

    def test_return_false_when_nested_validation_fails(self):
        self.validator = NestedStackValidator(self.cf_conn, 'test_bad.json')
        self.assertFalse(self.validator.validate())


if __name__ == '__main__':
    unittest.main()
