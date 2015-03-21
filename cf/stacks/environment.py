class Environment(object):
    def __init__(self, service, **options):
        self.service = service
        self.env = options['environment']
        self.name = options['name']
        self.bucket_name = self.service.build_s3_bucket_name(self)
        self.template = self.name + '.json'
        self.capabilities = ['CAPABILITY_IAM']
        self.stack_name = self.service.build_stack_name(self)
        self.template_uri = self.service.build_template_uri(self)
        self.template_body = self.service.load_template_body(self)
        self.tags = self.service.build_tags(self)
        self.inputs = self.service.build_inputs(self)
        self.params = self.service.build_params(self)
        self.topic_name = self.service.build_topic_name(self)
        self.public_internal_domain = 'gocurb.io' if self.env == 'prod' else self.env + '.gocurb.io'

    def validate(self):
        return self.service.validate(self)

    def describe(self):
        return self.service.describe(self)

    def delete(self):
        return self.service.delete(self)

    def create(self):
        return self.service.create(self)

    def update(self):
        return self.service.update(self)


class BootstrapEnvironment(object):
    def __init__(self, service, **options):
        self.service = service
        self.env = options['environment']
        self.bucket_name = self.service.build_s3_bucket_name(self)
        self.topic_name = self.service.build_topic_name(self)

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
