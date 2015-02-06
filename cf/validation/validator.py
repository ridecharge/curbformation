import json
import time
from boto.exception import BotoServerError

def new_nested_stack_validator(cf_conn):
    pass


class NestedStackValidator(object):
    def __init__(self, conn, template_path):
        self.conn = conn
        self.template_path = template_path
        self.template = self.__template()
        self.stack_resources = self.__stack_resources()
        self.dependencies = self.__dependencies()
        self.inputs = self.__inputs()
        self.default_inputs = self.__default_inputs()

    def __inputs(self):
        """
        :return: All parameters in the template
        """
        return set(self.template['Parameters'].keys())

    def __default_inputs(self):
        """
        Determine which inputs have default values
        :return: list of inputs that have default values
        """
        inputs = []
        for key, val in self.template['Parameters'].items():
            if 'Default' in val:
                inputs.append(key)
        return set(inputs)

    def __template(self):
        """
        Load the template body
        :return:
        """
        with open(self.template_path) as file:
            json_data = json.load(file)
        return json_data

    def __dependencies(self):
        """
        :return: the dependencies in a nested stacks resource parameter section
        """
        dependencies = {}
        for resource in self.stack_resources:
            properties = resource['Properties']
            template_url = properties['TemplateURL']['Fn::Join'][1][-1]
            params = properties['Parameters'].keys()
            dependencies[template_url] = set(params)
        return dependencies

    def __stack_resources(self):
        """
        Gets the items in resource block in the cloudformation template that is a nested stack
        :return: array of nested stack resources
        """
        resources = []
        for _, value in self.template['Resources'].items():
            if value['Type'] == 'AWS::CloudFormation::Stack':
                resources.append(value)
        return resources

    def __handle_errors(self, undefined_inputs, undefined_params, nested_path):
        has_errors = False
        if len(undefined_params) == 0 and len(undefined_inputs) == 0:
            print('Successfully validated {} nesting {}'.format(self.template_path, nested_path))
        else:
            if len(undefined_inputs) > 0:
                print('The following parameters are not defined in the nested template.')
                print('{0} nested in {1}'.format(nested_path, self.template_path))
                print(undefined_inputs)
                has_errors = True
            if len(undefined_params) > 0:
                print('The following parameters are missing inputs to the nested template.')
                print('{0} nested in {1}'.format(nested_path, self.template_path))
                print(undefined_params)
                has_errors = True
        return has_errors

    def __validate_template_syntax(self):
        """
        Validates a templates syntax using the boto/aws validation
        :returns True if the template syntax is valid
        """
        time.sleep(1)
        try:
            self.conn.validate_template(json.dumps(self.template))
        except BotoServerError as err:
            print(err.message)
            return False
        return True

    def validate(self):
        """
        Validates a stacks syntax and input/output match ups for nested stacks resursively
        :return: True if all the stacks come back valid
        """
        if self.__validate_template_syntax():
            nested_valid = True
            # Then check if the nested templates are valid
            for path, params in self.dependencies.items():
                nested_stack = NestedStackValidator(self.conn, path)
                # If the nested template validate properly then validated the in/out params
                if nested_stack.validate():
                    undefined_inputs = params.difference(nested_stack.inputs)
                    undefined_params = nested_stack.inputs.difference(params).difference(
                        nested_stack.default_inputs)
                    nested_valid = nested_valid and not self.__handle_errors(undefined_inputs,
                                                                             undefined_params, path)
                else:
                    nested_valid = False
            return nested_valid
        return False
