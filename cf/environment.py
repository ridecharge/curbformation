import cf.helpers
from subprocess import call

class Environment(object):
    def __init__(self, service, **options):
        self.service = service
        self.env = options['environment']
        self.bucket_name = cf.helpers.s3_bucket_name(self.env)
        self.topic_name = cf.helpers.topic_name(self.env)

    def bootstrap(self):
        self.service.create_s3_bucket(self)
        self.service.sync_s3_bucket(self)
        self.service.create_sns_topics(self)
        self.service.create_key_pair(self)

    def cleanup(self):
        self.service.delete_sns_topic(self)
        self.service.delete_s3_bucket(self)
        self.service.delete_key_pair(self)

    def sync(self):
        self.service.sync_s3_bucket(self)


class EnvironmentService(object):
    def __init__(self, ec2_conn, s3_conn, sns_conn):
        self.ec2_conn = ec2_conn
        self.s3_conn = s3_conn
        self.sns_conn = sns_conn

    def create_s3_bucket(self, bootstrap):
        print("Creating S3 Bucket:", bootstrap.bucket_name)
        self.s3_conn.create_bucket(bootstrap.bucket_name)

    def delete_s3_bucket(self, bootstrap):
        print("Deleting S3 Bucket and contents:", bootstrap.bucket_name)
        call(['aws', 's3', 'rm', 's3://' + bootstrap.bucket_name, '--recursive'])
        self.s3_conn.delete_bucket(bootstrap.bucket_name)

    def create_sns_topics(self, bootstrap):
        print("Creating SNS Topic:", bootstrap.topic_name)
        self.sns_conn.create_topic(bootstrap.topic_name)

    def delete_sns_topic(self, bootstrap):
        print("Deleting SNS Topic:", bootstrap.topic_name)
        self.sns_conn.delete_topic('arn:aws:sns:us-east-1:563891166287:' + bootstrap.topic_name)

    def create_key_pair(self, bootstrap):
        print("Creating key pair:", bootstrap.env)
        try:
            self.ec2_conn.create_key_pair(bootstrap.env)
        except:
            print("Key pair exists skipping.")

    def delete_key_pair(self, bootstrap):
        print("Deleting key pair:", bootstrap.env)
        self.ec2_conn.delete_key_pair(bootstrap.env)

    def sync_s3_bucket(self, bootstrap):
        call(['aws', 's3', 'sync', '../{}-templates'.format(self.namespace),
              's3://' + bootstrap.bucket_name, '--delete', '--exclude', '*', '--include', '*.json'])

