#!/usr/bin/env python3
import unittest
from cf.environment import Environment
from cf.environment import EnvironmentService
from unittest.mock import MagicMock


class EnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.service = MagicMock()
        self.env = 'test'
        self.options = {'environment': self.env, 'region': 'us-east-1', 'account_id': '123'}
        self.bootstrap = Environment(self.service, **self.options)

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


class EnvironmentServiceTest(unittest.TestCase):
    def setUp(self):
        self.ec2_conn = MagicMock()
        self.s3_conn = MagicMock()
        self.sns_conn = MagicMock()
        self.service = EnvironmentService(self.ec2_conn, self.s3_conn, self.sns_conn)
        self.bootstrap = MagicMock()
        self.bootstrap.env = 'env'
        self.bootstrap.topic_name = 'topic'
        self.bootstrap.bucket_name = 'bucket'

    def test_create_s3_bucket(self):
        self.service.create_s3_bucket(self.bootstrap)
        self.s3_conn.create_bucket.assert_called_with(self.bootstrap.bucket_name)

    def test_create_sns_topic(self):
        self.service.create_sns_topics(self.bootstrap)
        self.sns_conn.create_topic.assert_called_with(self.bootstrap.topic_name)

    def test_create_key_pair(self):
        self.service.create_key_pair(self.bootstrap)
        self.ec2_conn.create_key_pair.assert_called_with(self.bootstrap.env)

    def test_delete_key_pair(self):
        self.service.delete_key_pair(self.bootstrap)
        self.ec2_conn.delete_key_pair.assert_called_with(self.bootstrap.env)


if __name__ == '__main__':
    unittest.main()
