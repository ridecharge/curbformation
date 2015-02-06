#!/usr/bin/env python3
import unittest
import cf.stacks.service
import cf.stacks.environment
from unittest.mock import MagicMock


class StackServiceTest(unittest.TestCase):
    def setUp(self):
        self.ec2_conn = MagicMock()
        self.cf_conn = MagicMock()
        self.cf_conn.update_stack = MagicMock(return_value="")
        self.cf_conn.create_stack = MagicMock(return_value="")
        self.stack = MagicMock()
        self.stack.env = 'test'
        self.stack.template = 'env.json'
        self.stack.stack_name = self.stack.env+'-env'
        self.stack.capabilities = ['CAPABILITY_IAM']
        self.stack.tags = {
            'Environment': self.stack.env,
            'Template': self.stack.template
        }
        self.stack.params = [('Environment', self.stack.env)]
        self.stack.template_uri = 'https://s3.amazonaws.com/curbformation-test-templates/env.json'
        self.service = cf.stacks.service.new_stack_service(self.cf_conn, self.ec2_conn)

    def test_create_key_pair(self):
        self.service.create_key_pair(self.stack)
        self.ec2_conn.create_key_pair.assert_called_with(self.stack.env)

    def test_delete_key_pair(self):
        self.service.delete_key_pair(self.stack)
        self.ec2_conn.delete_key_pair.assert_called_with(self.stack.env)

    def test_create(self):
        self.service.create(self.stack)
        self.cf_conn.create_stack. \
            assert_called_with(self.stack.stack_name,
                               None,
                               self.stack.template_uri,
                               self.stack.params,
                               capabilities=self.stack.capabilities,
                               tags=self.stack.tags,
                               disable_rollback=True)

    def test_update(self):
        self.service.update(self.stack)
        self.cf_conn.update_stack. \
            assert_called_with(self.stack.stack_name,
                               None,
                               self.stack.template_uri,
                               self.stack.params,
                               capabilities=self.stack.capabilities,
                               tags=self.stack.tags,
                               disable_rollback=True)

    def test_delete(self):
        self.service.delete(self.stack)
        self.cf_conn.delete_stack.assert_called_with(self.stack.stack_name)

    def test_describe(self):
        self.service.describe(self.stack)
        self.cf_conn.describe_stacks.assert_called_with(self.stack.stack_name)


if __name__ == '__main__':
    unittest.main()
