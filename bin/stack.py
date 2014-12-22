from enum import Enum
from boto import cloudformation

class Stack(object):

    class Types(Enum):
        iam = 1
        network = 2
        app = 3
        infra = 4

    STACK_DEPENDS_ON = "STACK_DEPENDS_ON"
    STACK_INPUTS = "STACK_INPUTS"
    STACK_CAPABILITIES = "STACK_CAPABILITIES"

    STACK_DEPENDENCIES = {
        Types.network:
        {
            STACK_INPUTS: ["NATRoleProfileId"],
            STACK_DEPENDS_ON: [Types.iam],
            STACK_CAPABILITIES: []
        },
        Types.iam:
        {
            STACK_INPUTS: [],
            STACK_DEPENDS_ON: [],
            STACK_CAPABILITIES: ["CAPABILITY_IAM"]
        }
    }

    def __init__(self, type, env, region="us-east-1"):
        self.env = env
        self.type = type
        self.cf_conn = cloudformation.connect_to_region(region)

    def depends_on(self):
        if self.type not in Stack.STACK_DEPENDENCIES:
            return None
        stack_types = Stack.STACK_DEPENDENCIES[
            self.type][Stack.STACK_DEPENDS_ON]
        stacks = []
        for type in stack_types:
            stacks.append(
                Stack(type, 'global' if type == Stack.Types.iam else self.env))
        return stacks

    def capabilities(self):
        if self.type not in Stack.STACK_DEPENDENCIES:
            return None
        return Stack.STACK_DEPENDENCIES[self.type][Stack.STACK_CAPABILITIES]

    def inputs(self):
        if self.type not in Stack.STACK_DEPENDENCIES:
            return None
        return Stack.STACK_DEPENDENCIES[self.type][Stack.STACK_INPUTS]

    def stack_name(self):
        return self.env + "-" + self.type.name

    def template_uri(self):
        return "https://s3.amazonaws.com/curbformation-" + \
            self.env + "-templates/" + self.type.name + ".json"

    def params(self):
        if not self.depends_on():
            return None

        params = [("Environment", self.env)]
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
        return self.cf_conn.describe_stacks(self.stack_name())[0]

    def create(self):
        return self.cf_conn.create_stack(
            self.stack_name(), None, self.template_uri(), self.params(), None, None, 30, self.capabilities())

    def update(self):
        return self.cf_conn.update_stack(
            self.stack_name(), None, self.template_uri(), self.params(), None, None, 30, self.capabilities())
