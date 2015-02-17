class Environment(object):
    def __init__(self, service, **options):
        self.service = service
        self.env = options['environment']
        self.name = options['name']
        self.template = self.name + '.json'
        self.capabilities = ['CAPABILITY_IAM']
        self.stack_name = self.service.build_stack_name(self)
        self.template_uri = self.service.build_template_uri(self)
        self.template_body = self.service.load_template_body(self)
        self.tags = self.service.build_tags(self)
        self.inputs = self.service.build_inputs(self)
        self.params = self.service.build_params(self)
        self.public_internal_domain = 'gocurb.io' if self.env == 'prod' else self.env + '.gocurb.io'

    def validate(self):
        return self.service.validate(self)

    def describe(self):
        return self.service.describe(self)

    def delete(self):
        self.service.delete_key_pair(self)
        self.service.delete_dynamic_record_sets(self)
        return self.service.delete(self)

    def create(self):
        self.service.create_key_pair(self)
        return self.service.create(self)

    def update(self):
        return self.service.update(self)
