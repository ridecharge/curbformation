import json
import time
import cf.helpers
from boto.exception import BotoServerError


class NestedStackValidator(object):
    def __init__(self, conn):
        self.conn = conn

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

    def __validate(self, template_body, template_path):
        """
        Validates a stacks syntax and input/output match ups for nested stacks resursively
        :return: True if all the stacks come back valid
        """
        if self.__validate_template_syntax(template_body, template_path):
            nested_valid = True
            for path, params in cf.helpers.nested_stack_dependencies(template_body):
                depend_template_body = cf.helpers.template_body(path)
                if self.__validate(depend_template_body, path):
                    inputs = cf.helpers.inputs(depend_template_body)
                    default_inputs = cf.helpers.default_inputs(depend_template_body)

                    undefined_inputs = params.difference(inputs)
                    undefined_params = inputs.difference(params).difference(default_inputs)
                    nested_valid = nested_valid and not handle_errors(undefined_inputs,
                                                                      undefined_params,
                                                                      path,
                                                                      template_path)
                else:
                    nested_valid = False
            return nested_valid
        return False

    def validate(self, stack):
        return self.__validate(stack.template_body, stack.template)


def handle_errors(undefined_inputs, undefined_params, path, template_path):
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
