import cf.helpers
from subprocess import call


class Environment(object):
    def __init__(self, service, options):
        self.service = service
        self.env = options.environment
        self.region = options.region
        self.config = cf.helpers.config(self.env)
        self.account_id = self.config['AccountId']
        self.bucket_name = cf.helpers.s3_bucket_name(self.env)
        self.topic_name = cf.helpers.topic_name(self.env)
        self.topic_arn = cf.helpers.topic_arn(self.env, self.region, self.account_id)

    def bootstrap(self):
        self.service.create_s3_bucket(self.bucket_name)
        self.service.create_sns_topics(self.topic_name)
        self.service.create_key_pair(self.env)

    def cleanup(self):
        self.service.delete_sns_topic(self.topic_arn)
        self.service.delete_s3_bucket(self.bucket_name)
        self.service.delete_key_pair(self.env)

    def sync(self):
        self.service.sync_s3_bucket(self.bucket_name)


class EnvironmentService(object):
    def __init__(self, ec2_conn, s3_conn, sns_conn):
        self.ec2_conn = ec2_conn
        self.s3_conn = s3_conn
        self.sns_conn = sns_conn

    def create_s3_bucket(self, bucket_name):
        print("Creating S3 Bucket:", bucket_name)
        self.s3_conn.create_bucket(bucket_name)

    def delete_s3_bucket(self, bucket_name):
        print("Deleting S3 Bucket and contents:", bucket_name)
        call(['aws', 's3', 'rm', 's3://' + bucket_name, '--recursive'])
        self.s3_conn.delete_bucket(bucket_name)

    def create_sns_topics(self, topic_name):
        print("Creating SNS Topic:", topic_name)
        self.sns_conn.create_topic(topic_name)

    def delete_sns_topic(self, topic_arn):
        print("Deleting SNS Topic:", topic_arn)
        self.sns_conn.delete_topic(topic_arn)

    def create_key_pair(self, env):
        print("Creating key pair:", env)
        try:
            self.ec2_conn.create_key_pair(env)
        except:
            print("Key pair exists skipping.")

    def delete_key_pair(self, env):
        print("Deleting key pair:", env)
        self.ec2_conn.delete_key_pair(env)

