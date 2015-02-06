import json
import time
from boto.exception import BotoServerError

def new_nested_stack_validator(cf_conn):
    pass


class NestedStackValidator(object):
    def __init__(self, conn, template_path):
        self.conn = conn
        self.template_path = template_path

    def __inputs(self, template_body):
        """
        :return: All parameters in the template
        """
        return set(template_body['Parameters'].keys())

    def __default_inputs(self, template_body):
        """
        Determine which inputs have default values
        :return: list of inputs that have default values
        """
        inputs = []
        for key, val in template_body['Parameters'].items():
            if 'Default' in val:
                inputs.append(key)
        return set(inputs)


    def __dependencies(self, template_body):
        """
        :return: the dependencies in a nested stacks resource parameter section
        """
        dependencies = {}
        for resource in self.__stack_resources(template_body):
            properties = resource['Properties']
            template_url = properties['TemplateURL']['Fn::Join'][1][-1]
            dependencies[template_url] = self.__inputs(template_body)
        return dependencies.items()

    def __stack_resources(self, template_body):
        """
        Gets the items in resource block in the cloudformation template that is a nested stack
        :return: array of nested stack resources
        """
        resources = []
        for _, value in template_body['Resources'].items():
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

    def __validate_template_syntax(self, template_body):
        """
        Validates a templates syntax using the boto/aws validation
        :returns True if the template syntax is valid
        """
        time.sleep(1)
        try:
            self.conn.validate_template(json.dumps(template_body))
        except BotoServerError as err:
            print(err.message)
            return False
        return True

    def __load_template(self, path):
        return json.load(open('../curbformation/'+path))

    def __validate(self, template_body):
        """
        Validates a stacks syntax and input/output match ups for nested stacks resursively
        :return: True if all the stacks come back valid
        """
        if self.__validate_template_syntax(template_body):
            for path, params in self.__dependencies(template_body):
                depend_template_body = self.__load_template(path)
                self.__validate(depend_template_body)

    def validate(self, stack):
        return self.__validate(stack.template_body)
