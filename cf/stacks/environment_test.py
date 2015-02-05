#!/usr/bin/env python3
import unittest
from cf.stacks.environment import Environment
from unittest.mock import MagicMock


class EnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.ec2_conn = MagicMock()
        self.cf_conn = MagicMock()
        self.cf_conn.update_stack = MagicMock(return_value="")
        self.cf_conn.create_stack = MagicMock(return_value="")
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
        self.environment = Environment(self.cf_conn, self.ec2_conn, self.env)

    def test_create(self):
        self.environment.create()
        self.ec2_conn.create_key_pair.assert_called_with(self.env)
        self.cf_conn.create_stack. \
            assert_called_with(self.stack_name,
                               None,
                               self.template_uri,
                               self.params,
                               capabilities=self.capabilities,
                               tags=self.tags,
                               disable_rollback=True)

    def test_update(self):
        self.environment.update()
        self.cf_conn.update_stack. \
            assert_called_with(self.stack_name,
                               None,
                               self.template_uri,
                               self.params,
                               capabilities=self.capabilities,
                               tags=self.tags,
                               disable_rollback=True)

    def test_delete(self):
        self.environment.delete()
        self.ec2_conn.delete_key_pair.assert_called_with(self.env)
        self.cf_conn.delete_stack.assert_called_with(self.stack_name)

    def test_describe(self):
        self.environment.describe()
        self.cf_conn.describe_stacks.assert_called_with(self.stack_name)


if __name__ == '__main__':
    unittest.main()
