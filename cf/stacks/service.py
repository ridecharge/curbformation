import json

def new_stack_service(cf_conn, ec2_conn):
    return StackService(cf_conn, ec2_conn)


class StackService(object):
    def __init__(self, cf_conn, ec2_conn, validator=None):
        self.cf_conn = cf_conn
        self.ec2_conn = ec2_conn
        self.validator = validator

    def build_full_stack_name(self, stack):
        full_name = ["{0.env}", "{0.name}"]
        return "-".join(full_name).format(stack)

    def build_template_uri(self, stack):
        uri = "https://s3.amazonaws.com/curbformation-{0.env}-templates/{0.template}"
        return uri.format(stack)

    def build_base_tags(self, stack):
        tag = {
            'Environment': stack.env,
            'Template': stack.template
        }
        return tag

    def build_inputs(self, stack):
        data = json.load(open(stack.template))
        inputs = []
        for key in data['Parameters']:
            inputs.append(key)
        return inputs

    def build_params(self, stack):
        # All stacks have the environment param, and
        # stacks with more inputs will call out and get them
        # from the environment stack
        params = [('Environment', stack.env)]
        if len(stack.inputs) > 1:
            for output in self.__describe(stack.env+'-env'):
                if output.key != 'Environment':
                    params.append((output.key, output.value))

    def create_key_pair(self, stack):
        print("Creating key pair {0}".format(stack.env))
        self.ec2_conn.create_key_pair(stack.env)

    def delete_key_pair(self, stack):
        print("Deleting key pair {0}".format(stack.env))
        self.ec2_conn.delete_key_pair(stack.env)

    def __describe(self, stack_name):
        return self.cf_conn.describe_stacks(stack_name)[0]

    def validate(self, stack):
        self.validator.validate(stack)

    def describe(self, stack):
        print("Describing {0}".format(stack.stack_name))
        return self.__describe(stack.stack_name)

    def delete(self, stack):
        print("Deleting {0}".format(stack.stack_name))
        return self.cf_conn.delete_stack(stack.stack_name)

    def create(self, stack):
        print("Creating {0}".format(stack.stack_name))
        return self.cf_conn.create_stack(
            stack.stack_name,
            None,
            stack.template_uri,
            stack.params,
            capabilities=stack.capabilities,
            tags=stack.tags,
            disable_rollback=True
        )

    def update(self, stack):
        print("Updating {0}".format(stack.stack_name))
        return self.cf_conn.update_stack(
            stack.stack_name,
            None,
            stack.template_uri,
            stack.params,
            capabilities=stack.capabilities,
            tags=stack.tags,
            disable_rollback=True
        )
