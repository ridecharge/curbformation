import cf.stacks.service


def new_environment_stack(cf_conn, ec2_conn, env):
    service = cf.stacks.service.new_stack_service(cf_conn, ec2_conn)
    return Environment(service, env)


class Environment(object):
    def __init__(self, service, env):
        self.service = service
        self.env = env
        self.name = 'env'
        self.template = 'env.json'
        self.capabilities = ['CAPABILITY_IAM']
        self.stack_name = self.service.build_full_stack_name(self)
        self.template_uri = self.service.build_template_uri(self)
        self.tags = self.service.build_base_tags(self)
        self.inputs = self.service.build_inputs(self)
        self.params = self.service.build_params(self)

    def validate(self):
        return self.service.validate(self)

    def describe(self):
        return self.service.describe(self)

    def delete(self):
        self.service.delete_key_pair(self)
        return self.service.delete(self)

    def create(self):
        self.service.create_key_pair(self)
        return self.service.create(self)

    def update(self):
        return self.service.update(self)
