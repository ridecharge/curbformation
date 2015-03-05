#!/usr/bin/env python3
import unittest
from cf.stacks.environment import Environment
from cf.stacks.environment import BootstrapEnvironment
from unittest.mock import MagicMock


class EnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.service = MagicMock()
        self.env = 'test'
        self.template = 'env.json'
        self.name = 'env'
        self.stack_name = self.env + '-env'
        self.capabilities = ['CAPABILITY_IAM']
        self.tags = {
            'Environment': self.env,
            'Template': self.template
        }
        self.params = [('Environment', self.env)]
        self.template_uri = 'https://s3.amazonaws.com/curbformation-test-templates/env.json'
        self.options = {'environment': self.env, 'name': self.name}
        self.environment = Environment(self.service, **self.options)

    def test_validate(self):
        self.environment.validate()
        self.service.validate(self.environment)

    def test_create(self):
        self.environment.create()
        self.service.create(self.environment)

    def test_update(self):
        self.environment.update()
        self.service.update.assert_called_with(self.environment)

    def test_delete(self):
        self.environment.delete()
        self.service.delete.assert_called_with(self.environment)

    def test_describe(self):
        self.environment.describe()
        self.service.describe.assert_called_with(self.environment)


class BootstrapEnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.service = MagicMock()
        self.env = 'test'
        self.options = {'environment': self.env}
        self.bootstrap = BootstrapEnvironment(self.service, **self.options)

    def test_sync(self):
        self.bootstrap.sync()
        self.service.sync_s3_bucket.assert_called_with(self.bootstrap)

    def test_bootstrap(self):
        self.bootstrap.bootstrap()
        self.service.create_s3_bucket.assert_called_with(self.bootstrap)
        self.service.sync_s3_bucket.assert_called_with(self.bootstrap)
        self.service.create_sns_topics.assert_called_with(self.bootstrap)
        self.service.create_key_pair.assert_called_with(self.bootstrap)

    def test_cleanup(self):
        self.bootstrap.cleanup()
        self.service.delete_key_pair.assert_called_with(self.bootstrap)
        self.service.delete_s3_bucket.assert_called_with(self.bootstrap)
        self.service.delete_sns_topic.assert_called_with(self.bootstrap)


if __name__ == '__main__':
    unittest.main()
