#!/usr/bin/env python3
import unittest
from cf.stacks.environment import Environment
from unittest.mock import MagicMock


class ApplicationTest(unittest.TestCase):
    def setUp(self):
        self.service = MagicMock()
        self.env = 'test'
        self.name = 'env'
        self.template = 'env.json'
        self.stack_name = self.env + '-env'
        self.capabilities = ['CAPABILITY_IAM']
        self.tags = {
            'Environment': self.env,
            'Template': self.template
        }
        self.params = [('Environment', self.env)]
        self.template_uri = 'https://s3.amazonaws.com/curbformation-test-templates/env.json'
        self.options = {'environment': 'self.env', 'name':self.name}
        self.stack = Environment(self.service, **self.options)

    def test_validate(self):
        self.stack.validate()
        self.service.validate(self.stack)

    def test_create(self):
        self.stack.create()
        self.service.create(self.stack)

    def test_update(self):
        self.stack.update()
        self.service.update.assert_called_with(self.stack)

    def test_delete(self):
        self.stack.delete()
        self.service.delete.assert_called_with(self.stack)

    def test_describe(self):
        self.stack.describe()
        self.service.describe.assert_called_with(self.stack)


if __name__ == '__main__':
    unittest.main()
