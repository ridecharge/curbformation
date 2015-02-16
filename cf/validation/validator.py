import json
import time
from boto.exception import BotoServerError


class NestedStackValidator(object):
    def __init__(self, conn, root_path='../curbformation-templates/'):
        self.conn = conn
        self.root_path = root_path

    def __inputs(self, template_body):
        """
        :return: All parameters in the template
        """
        return set(template_body['Parameters'].keys())

    def __default_inputs(self, template_body):
        """
        :return: set of inputs that have default values
        """
        return set(key for key, val in template_body['Parameters'].items() if 'Default' in val)

    def __dependencies(self, template_body):
        """
        :return: the dependencies in a nested stacks resource parameter section
        """
        dependencies = {}
        for resource in self.__stack_resources(template_body):
            properties = resource['Properties']
            template_url = properties['TemplateURL']['Fn::Join'][1][-1]
            dependencies[template_url] = self.__inputs(properties)
        return dependencies.items()

    def __stack_resources(self, template_body):
        """
        :return: array of nested stack resources
        """
        return [val for val in template_body['Resources'].values() if
                val['Type'] == 'AWS::CloudFormation::Stack']

    def __handle_errors(self, undefined_inputs, undefined_params, path, template_path):
        has_errors = False
        if len(undefined_params) == 0 and len(undefined_inputs) == 0:
            print('Successfully validated {} nesting {}'.format(template_path, path))
        else:
            if len(undefined_inputs) > 0:
                print('The following parameters are not defined in the nested template.')
                print('{0} nested in {1}'.format(path, template_path))
                print(undefined_inputs)
                has_errors = True
            if len(undefined_params) > 0:
                print('The following parameters are missing inputs to the nested template.')
                print('{0} nested in {1}'.format(path, template_path))
                print(undefined_params)
                has_errors = True
        return has_errors

    def __validate_template_syntax(self, template_body, path):
        """
        Validates a templates syntax using the boto/aws validation
        :returns True if the template syntax is valid
        """
        time.sleep(1)
        try:
            self.conn.validate_template(json.dumps(template_body))
        except BotoServerError as err:
            print(path)
            print(err.message)
            return False
        return True

    def __load_template(self, path):
        with open(self.root_path + path) as f:
            return json.load(f)

    def __validate(self, template_body, template_path):
        """
        Validates a stacks syntax and input/output match ups for nested stacks resursively
        :return: True if all the stacks come back valid
        """

        if self.__validate_template_syntax(template_body, template_path):
            nested_valid = True
            for path, params in self.__dependencies(template_body):
                depend_template_body = self.__load_template(path)
                if self.__validate(depend_template_body, path):
                    inputs = self.__inputs(depend_template_body)
                    default_inputs = self.__default_inputs(depend_template_body)

                    undefined_inputs = params.difference(inputs)
                    undefined_params = inputs.difference(params).difference(default_inputs)
                    nested_valid = nested_valid and not self.__handle_errors(undefined_inputs,
                                                                             undefined_params,
                                                                             path,
                                                                             template_path)
                else:
                    nested_valid = False
            return nested_valid
        return False

    def validate(self, stack):
        return self.__validate(stack.template_body, stack.template)
