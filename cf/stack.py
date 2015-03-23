import json
import cf.helpers
from os.path import expanduser


class Stack(object):
    def __init__(self, service, **options):
        self.service = service
        self.env = options['environment']
        self.name = options['name']
        self.template = self.name + '.json'
        self.capabilities = ['CAPABILITY_IAM']
        self.bucket_name = cf.helpers.s3_bucket_name(self.env)
        self.stack_name = cf.helpers.stack_name(self.env, self.name)
        self.template_uri = cf.helpers.template_uri(self.bucket_name, self.template)
        self.template_body = cf.helpers.template_body(self.template)
        self.tags = cf.helpers.tags(self.env, self.template)
        self.inputs = cf.helpers.inputs(self.template_body)
        self.params = self.service.build_params(self)
        self.topic_arn = cf.helpers.topic_arn(self.env)

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


class StackService(object):
    def __init__(self, cf_conn, ec2_conn, validator, debug=False):
        self.cf_conn = cf_conn
        self.ec2_conn = ec2_conn
        self.validator = validator
        self.debug = debug

    def build_params(self, stack):
        # All stacks have the environment param, and
        # stacks with more inputs will call out and get them
        # from the environment stack
        params = [('Environment', stack.env)]
        if stack.name == 'env':
            return params + self.__read_config(stack)
        else:
            if 'ApplicationName' in stack.inputs:
                params.append(('ApplicationName', stack.name))
            return params + [(out.key, out.value) for out in
                             self.__describe(stack.env + '-env').outputs if
                             out.key in stack.inputs]

    def __read_config(self, stack):
        config_path = expanduser("~") + "/.cf/" + stack.env + ".json"
        print("Using config:", config_path)
        with open(config_path, 'r') as f:
            return list(json.load(f).items())

    def validate(self, stack):
        return self.validator.validate(stack)

    def __describe(self, stack_name):
        return self.cf_conn.describe_stacks(stack_name)[0]

    def describe(self, stack):
        print("Describing:", stack.stack_name)
        return self.__describe(stack.stack_name)

    def delete(self, stack):
        print("Deleting:", stack.stack_name)
        return self.cf_conn.delete_stack(stack.stack_name)

    def create(self, stack):
        print(stack.template_uri)
        print("Creating:", stack.stack_name)
        print("with params:", stack.params)
        return self.cf_conn.create_stack(
            stack.stack_name,
            template_url=stack.template_uri,
            parameters=stack.params,
            capabilities=stack.capabilities,
            tags=stack.tags,
            disable_rollback=self.debug,
            notification_arns=stack.topic_arn
        )

    def update(self, stack):
        print("Updating:", stack.stack_name)
        print("with params:", stack.params)
        return self.cf_conn.update_stack(
            stack.stack_name,
            template_url=stack.template_uri,
            parameters=stack.params,
            capabilities=stack.capabilities,
            tags=stack.tags,
            disable_rollback=self.debug,
            notification_arns=stack.topic_arn
        )
