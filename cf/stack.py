from enum import Enum


class Stack(object):
    class Types(Enum):
        iam = 1
        network = 2
        apps = 3
        infra = 4

    STACK_DEPENDS_ON = 'STACK_DEPENDS_ON'
    STACK_INPUTS = 'STACK_INPUTS'
    STACK_CAPABILITIES = 'STACK_CAPABILITIES'
    STACK_DYNAMIC_INPUTS = 'STACK_DYNAMIC_INPUTS'

    ENV_GLOBAL = 'global'
    TYPES_GLOBAL = [Types.iam]

    STACK_DEPENDENCIES = {
        Types.network: {
            STACK_INPUTS: ['NATInstanceProfile'],
            STACK_DYNAMIC_INPUTS: [],
            STACK_DEPENDS_ON: [Types.iam],
            STACK_CAPABILITIES: []
        },
        Types.iam: {
            STACK_INPUTS: [],
            STACK_DYNAMIC_INPUTS: [],
            STACK_DEPENDS_ON: [],
            STACK_CAPABILITIES: ['CAPABILITY_IAM']
        },
        Types.apps: {
            STACK_INPUTS: ['ApplicationVPC', 'ApplicationVPCDBSubnetGroup',
                           'ApplicationVPCPrivateSubnets'],
            STACK_DYNAMIC_INPUTS: ["{0.app_name}AppInstanceProfile"],
            STACK_DEPENDS_ON: [Types.network, Types.iam],
            STACK_CAPABILITIES: []
        }
    }

    def __init__(self, cf_conn, env, stack_type, app_name=None):
        if env == Stack.ENV_GLOBAL and stack_type not in Stack.TYPES_GLOBAL:
            raise Exception("Global environment without global stack type ({0.name}) specified"
                            .format(stack_type))

        if stack_type not in Stack.TYPES_GLOBAL and env == Stack.ENV_GLOBAL:
            env = Stack.ENV_GLOBAL
            print(
                "Warning: {0} stack passed in with non global environment.  Setting to global."
                .format(stack_type.name))

        self.env = env
        self.stack_type = stack_type
        self.app_name = app_name

        self.cf_conn = cf_conn

    def depends_on(self):
        if self.stack_type not in Stack.STACK_DEPENDENCIES:
            return []
        stack_types = Stack.STACK_DEPENDENCIES[
            self.stack_type][Stack.STACK_DEPENDS_ON]
        stacks = []
        for stack_type in stack_types:
            stacks.append(
                Stack(
                    self.cf_conn,
                    Stack.ENV_GLOBAL if stack_type in Stack.TYPES_GLOBAL else self.env,
                    stack_type
                ))
        return stacks

    def capabilities(self):
        if self.stack_type not in Stack.STACK_DEPENDENCIES:
            return None
        return Stack.STACK_DEPENDENCIES[self.stack_type][Stack.STACK_CAPABILITIES]

    def inputs(self):
        if self.stack_type not in Stack.STACK_DEPENDENCIES:
            return None
        inputs = Stack.STACK_DEPENDENCIES[self.stack_type][Stack.STACK_INPUTS].copy()
        for dynamic_input in Stack.STACK_DEPENDENCIES[self.stack_type][Stack.STACK_DYNAMIC_INPUTS]:
            inputs.append(dynamic_input.format(self))
        return inputs

    def stack_name(self):
        name = ["{0.env}", "{0.stack_type.name}"]
        if self.app_name:
            name.append("{0.app_name}")
        return "-".join(name).format(self)

    def template_uri(self):
        uri = "https://s3.amazonaws.com/curbformation-{0.env}-templates/{0.stack_type.name}.json"
        return uri.format(self)

    def tags(self):
        tag = {
            "Environment": self.env,
            "StackType": self.stack_type
        }
        if self.app_name:
            tag['Application'] = self.app_name
        return tag

    def params(self):
        if not self.depends_on():
            return None

        params = [('Environment', self.env)]
        for depend_stack in self.depends_on():
            params.extend(self.build_params(depend_stack))
        return params

    def build_params(self, depend_stack):
        params = []
        inputs = self.inputs()
        for output in depend_stack.describe().outputs:
            if output.key in inputs:
                params.append((output.key, output.value))
        return params

    def describe(self):
        print("Describing {0}".format(self.stack_name()))
        return self.cf_conn.describe_stacks(self.stack_name())[0]

    def delete(self):
        print("Deleting {0}".format(self.stack_name()))
        return self.cf_conn.delete_stack(self.stack_name())

    def create(self):
        print("Creating {0}".format(self.stack_name()))
        return self.cf_conn.create_stack(
            self.stack_name(),
            None,
            self.template_uri(),
            self.params(),
            capabilities=self.capabilities(),
            tags=self.tags()
        )

    def update(self):
        print("Updating {0}".format(self.stack_name()))
        return self.cf_conn.update_stack(
            self.stack_name(),
            None,
            self.template_uri(),
            self.params(),
            capabilities=self.capabilities(),
            tags=self.tags()
        )
