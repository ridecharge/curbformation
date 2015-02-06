#!/usr/bin/env python3
import unittest
from cf.stacks.environment import Environment
from unittest.mock import MagicMock


class EnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.service = MagicMock()
        self.env = 'test'
        self.template = 'env.json'
        self.stack_name = self.env+'-env'
        self.capabilities = ['CAPABILITY_IAM']
        self.tags = {
            'Environment': self.env,
            'Template': self.template
        }
        self.params = [('Environment', self.env)]
        self.template_uri = 'https://s3.amazonaws.com/curbformation-test-templates/env.json'
        self.environment = Environment(self.service, self.env)

    def test_create(self):
        self.environment.create()
        self.service.create_key_pair.assert_called_with(self.environment)
        self.service.create(self.environment)

    def test_update(self):
        self.environment.update()
        self.service.update.assert_called_with(self.environment)

    def test_delete(self):
        self.environment.delete()
        self.service.delete_key_pair.assert_called_with(self.environment)
        self.service.delete.assert_called_with(self.environment)

    def test_describe(self):
        self.environment.describe()
        self.service.describe.assert_called_with(self.environment)


if __name__ == '__main__':
    unittest.main()
