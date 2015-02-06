import cf.stacks.service


def new_application_stack(cf_conn, ec2_conn, app, env):
    service = cf.stacks.service.new_stack_service(cf_conn, ec2_conn)
    return Application(service, app, env)


class Application(object):
    def __init__(self, service, app, env):
        self.service = service
        self.app = app
        self.env = env
        self.name = app
        self.template = self.app+'.json'
        self.capabilities = ['CAPABILITY_IAM']
        self.stack_name = self.service.build_full_stack_name(self)
        self.template_uri = self.service.build_template_uri(self)
        self.template_body = self.service.load_template_body(self)
        self.tags = self.service.build_base_tags(self)
        self.params = self.service.build_params(self)

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
