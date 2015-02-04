from cf.validation.validator import NestedStackValidator

class Environment(object):

    def __init__(self, cf_conn, ec2_conn, env):
        self.cf_conn = cf_conn
        self.ec2_conn = ec2_conn
        self.env = env
        self.template = 'env.json'
        self.capabilities = ['CAPABILITY_IAM']
        self.stack_name = self.__full_stack_name()
        self.template_uri = self.__template_uri()
        self.tags = self.__tags()
        self.params = self.__params()

    def validate(self):
        return NestedStackValidator(self.cf_conn, self.template).validate()

    def __full_stack_name(self):
        full_name = ["{0.env}", "env"]
        return "-".join(full_name).format(self)

    def __template_uri(self):
        uri = "https://s3.amazonaws.com/curbformation-{0.env}-templates/{0.template}"
        return uri.format(self)

    def __tags(self):
        tag = {
            'Environment': self.env,
            'Template': self.template
        }
        return tag

    def __params(self):
        return [('Environment', self.env)]

    def __generate_key_pair(self):
        print("Creating key pair {0}".format(self.env))
        self.ec2_conn.create_key_pair(self.env)

    def __delete_key_pair(self):
        print("Deleting key pair {0}".format(self.env))
        self.ec2_conn.delete_key_pair(self.env)

    def describe(self):
        print("Describing {0}".format(self.stack_name))
        return self.cf_conn.describe_stacks(self.stack_name)[0]

    def delete(self):
        print("Deleting {0}".format(self.stack_name))
        self.__delete_key_pair()
        return self.cf_conn.delete_stack(self.stack_name)

    def create(self):
        print("Creating {0}".format(self.stack_name))
        self.__generate_key_pair()
        return self.cf_conn.create_stack(
            self.stack_name,
            None,
            self.template_uri,
            self.params,
            capabilities=self.capabilities,
            tags=self.tags,
            disable_rollback=True
        )

    def update(self):
        print("Updating {0}".format(self.stack_name))
        return self.cf_conn.update_stack(
            self.stack_name,
            None,
            self.template_uri,
            self.params,
            capabilities=self.capabilities,
            tags=self.tags,
            disable_rollback=True
        )
