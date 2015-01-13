from enum import Enum
import json
import os


class Stack(object):
    class Types(Enum):
        env = 1
        infra = 2
        api = 3

    APP_STACKS = [Types.api]

    STACK_DEPENDS_ON = 'STACK_DEPENDS_ON'
    STACK_CAPABILITIES = 'STACK_CAPABILITIES'

    STACK_DEPENDENCIES = {
        Types.env: {
            STACK_DEPENDS_ON: [],
            STACK_CAPABILITIES: ['CAPABILITY_IAM']
        },
        Types.infra: {
            STACK_DEPENDS_ON: [],
            STACK_CAPABILITIES: ['CAPABILITY_IAM']
        },
        Types.api: {
            STACK_DEPENDS_ON: [Types.env],
            STACK_CAPABILITIES: ['CAPABILITY_IAM']
        }
    }

    def __init__(self, cf_conn, stack_type, stack_name, env):
        self.env = env
        self.stack_type = stack_type
        self.stack_name = stack_name

        if self.stack_type not in Stack.APP_STACKS:
            self.env = self.stack_name

        self.cf_conn = cf_conn

    def depends_on(self):
        stacks = []
        depend_stack_types = Stack.STACK_DEPENDENCIES[self.stack_type][Stack.STACK_DEPENDS_ON]
        print("Depends On Stacks: ", *depend_stack_types)
        for depend_stack_type in depend_stack_types:
            stacks.append(
                Stack(
                    self.cf_conn,
                    depend_stack_type,
                    self.stack_name if depend_stack_type in Stack.APP_STACKS else self.env,
                    self.env
                ))
        return stacks

    def capabilities(self):
        return Stack.STACK_DEPENDENCIES[self.stack_type][Stack.STACK_CAPABILITIES]

    def inputs(self):
        data = json.load(open(
            "{0}/templates/{1}.json".format(os.environ.get('PYTHONPATH'), self.stack_type.name)))
        inputs = []
        for key in data['Parameters']:
            inputs.append(key)
        return inputs

    def full_stack_name(self):
        full_name = ["{0.env}", "{0.stack_type.name}"]
        if self.stack_type in Stack.APP_STACKS:
            full_name.append("{0.stack_name}")
        return "-".join(full_name).format(self)

    def template_uri(self):
        uri = "https://s3.amazonaws.com/curbformation-{0.env}-templates/{0.stack_type.name}.json"
        return uri.format(self)

    def tags(self):
        tag = {
            'Environment': self.env,
            'StackType': self.stack_type.name
        }
        if self.stack_type in Stack.APP_STACKS:
            tag['Application'] = self.stack_name
        return tag

    def params(self):
        params = [('Environment', self.env)]
        if self.stack_type in Stack.APP_STACKS:
            params.append(('ApplicationName', self.stack_name))
        for depend_stack in self.depends_on():
            params.extend(self.build_params(depend_stack))
        print("With Parameters: ", *params)
        return params

    def build_params(self, depend_stack):
        params = []
        inputs = self.inputs()
        for output in depend_stack.describe().outputs:
            if output.key in inputs:
                params.append((output.key, output.value))
        return params

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
            tags=self.tags()
        )

    def update(self):
        print("Updating {0}".format(self.full_stack_name()))
        return self.cf_conn.update_stack(
            self.full_stack_name(),
            None,
            self.template_uri(),
            self.params(),
            capabilities=self.capabilities(),
            tags=self.tags()
        )
