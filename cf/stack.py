
class EnvironmentStack(object):

    def __init__(self, cf_conn, env):
        self.cf_conn = cf_conn
        self.env = env
        self.template = 'env.json'

    def capabilities(self):
        return ['CAPABILITY_IAM']

    def full_stack_name(self):
        full_name = ["{0.env}", "env"]
        return "-".join(full_name).format(self)

    def template_uri(self):
        uri = "https://s3.amazonaws.com/curbformation-{0.env}-templates/{0.template}"
        return uri.format(self)

    def tags(self):
        tag = {
            'Environment': self.env,
            'Template': self.template
        }
        return tag

    def params(self):
        return [('Environment', self.env)]

    def describe(self):
        print("Describing {0}".format(self.full_stack_name()))
        return self.cf_conn.describe_stacks(self.full_stack_name())[0]

    def delete(self):
        print("Deleting {0}".format(self.full_stack_name()))
        return self.cf_conn.delete_stack(self.full_stack_name())

    def create(self):
        print("Creating {0}".format(self.full_stack_name()))
        return self.cf_conn.create_stack(
            self.full_stack_name(),
            None,
            self.template_uri(),
            self.params(),
            capabilities=self.capabilities(),
            tags=self.tags(),
            disable_rollback=True
        )

    def update(self):
        print("Updating {0}".format(self.full_stack_name()))
        return self.cf_conn.update_stack(
            self.full_stack_name(),
            None,
            self.template_uri(),
            self.params(),
            capabilities=self.capabilities(),
            tags=self.tags(),
            disable_rollback=True
        )
