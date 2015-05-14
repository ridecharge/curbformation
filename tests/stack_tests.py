import unittest
import cf.helpers
from cf.stack import Stack
from cf.stack import StackService
from unittest.mock import MagicMock


class StackTest(unittest.TestCase):
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
        cf.helpers.sync_s3_bucket = MagicMock()
        self.service.load_config = MagicMock(
            return_value={'environment': 'test', 'account_id': '123'})
        self.params = [('Environment', self.env)]
        self.template_uri = 'https://s3.amazonaws.com/curbformation-test-templates/env.json'
        self.options = MagicMock()
        self.options.environment = self.env
        self.options.region = 'us-east-1'
        self.options.account_id = '123'
        self.options.name = 'name'
        self.options.version = 'abc'
        self.stack = Stack(self.service, self.options)

    def test_validate(self):
        self.stack.validate()
        self.service.validate(self.stack)

    def test_create(self):
        self.stack.create()
        self.service.create(self.stack)

    def test_delete(self):
        self.stack.delete()
        self.service.delete.assert_called_with(self.stack.stack_name)

    def test_describe(self):
        self.stack.describe()
        self.service.describe.assert_called_with(self.stack.stack_name)


class StackServiceTest(unittest.TestCase):
    def setUp(self):
        self.ec2_conn = MagicMock()
        self.cf_conn = MagicMock()
        self.consul_conn = MagicMock()
        self.validator = MagicMock()
        self.cf_conn.update_stack = MagicMock(return_value="")
        self.cf_conn.create_stack = MagicMock(return_value="")
        self.validator.validate = MagicMock(return_value=True)
        self.stack = MagicMock()
        self.stack.env = 'test'
        self.stack.template = 'env.json'
        self.stack.topic_arn = 'topic'
        self.stack.stack_name = self.stack.env + '-env'
        self.stack.capabilities = ['CAPABILITY_IAM']
        self.stack.tags = {
            'Environment': self.stack.env,
            'Template': self.stack.template
        }
        self.stack.params = [('Environment', self.stack.env)]
        self.stack.template_uri = 'https://s3.amazonaws.com/curbformation-test-templates/env.json'
        self.service = StackService(self.cf_conn, self.ec2_conn, self.consul_conn, self.validator)

    def test_create(self):
        self.service.create(self.stack)
        self.cf_conn.create_stack. \
            assert_called_with(self.stack.stack_name,
                               template_url=self.stack.template_uri,
                               parameters=self.stack.params,
                               capabilities=self.stack.capabilities,
                               tags=self.stack.tags,
                               disable_rollback=False,
                               notification_arns=self.stack.topic_arn)

    def test_update(self):
        self.service.update(self.stack)
        self.cf_conn.update_stack. \
            assert_called_with(self.stack.stack_name,
                               template_url=self.stack.template_uri,
                               parameters=self.stack.params,
                               capabilities=self.stack.capabilities,
                               tags=self.stack.tags,
                               disable_rollback=False,
                               notification_arns=self.stack.topic_arn)

    def test_delete(self):
        self.service.delete(self.stack.stack_name)
        self.cf_conn.delete_stack.assert_called_with(self.stack.stack_name)

    def test_validate(self):
        self.service.validate(self.stack)
        self.validator.validate.assert_called_with(self.stack)

    def test_describe(self):
        self.service.describe(self.stack.stack_name)
        self.cf_conn.describe_stacks.assert_called_with(self.stack.stack_name)


if __name__ == '__main__':
    unittest.main()
