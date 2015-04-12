import cf.helpers
from http.client import HTTPSConnection


class Stack(object):
    VALID_DEPLOYMENT_STATES = ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE',
                               'ROLLBACK_COMPLETE']

    def __init__(self, service, options):
        self.service = service
        self.env = options.environment
        self.region = options.region
        self.name = options.name
        self.config = cf.helpers.config(self.env)
        self.account_id = self.config['account_id']
        self.template = self.name + '.json'
        self.capabilities = ['CAPABILITY_IAM']
        self.bucket_name = cf.helpers.s3_bucket_name(self.env)
        self.stack_name = cf.helpers.stack_name(self.env, self.name)
        self.template_uri = cf.helpers.template_uri(self.bucket_name, self.template)
        self.template_body = self.service.load_template_body(self.template)
        self.tags = cf.helpers.tags(self.env, self.template)
        self.inputs = cf.helpers.inputs(self.template_body)
        self.params = self.service.params(self)
        self.topic_arn = cf.helpers.topic_arn(self.env, self.region, self.account_id)
        self.options = options

    def validate(self):
        return self.service.validate(self)

    def describe(self):
        return self.service.describe(self.stack_name)

    def delete(self):
        return self.service.delete(self.stack_name)

    def create(self):
        cf.helpers.exit_when_invalid(self)
        cf.helpers.sync_s3_bucket(self.bucket_name)
        return self.service.create(self)

    def update(self):
        cf.helpers.exit_when_invalid(self)
        cf.helpers.sync_s3_bucket(self.bucket_name)
        return self.service.update(self)

    def is_deployable(self):
        return self.describe().stack_status in Stack.VALID_DEPLOYMENT_STATES

    def rollback(self):
        self.options.version = cf.helpers.previous_version(self.template_body)
        self.deploy()

    def redeploy(self):
        cf.helpers.update_serial_param(self.template_body, self.template)
        cf.helpers.sync_s3_bucket(self.bucket_name)
        return self.service.update(self)

    def deploy(self):
        if not self.is_deployable():
            print('The current stack is in progress of updating and cannot be deployed.')
            exit(1)
        cf.helpers.exit_when_invalid(self)
        if not self.service.update_template_versions(self.options.version, self):
            exit(1)
        cf.helpers.sync_s3_bucket(self.bucket_name)
        return self.service.update(self)

    def lock(self):
        self.service.lock(self.stack_name)

    def unlock(self):
        self.service.unlock(self.stack_name)


class StackService(object):
    def __init__(self, cf_conn, ec2_conn, validator, debug=False):
        self.cf_conn = cf_conn
        self.ec2_conn = ec2_conn
        self.validator = validator
        self.debug = debug

    def params(self, stack):
        if stack.name == 'env':
            return [('Environment', stack.env)] + list(stack.config['env_params'].items())
        else:
            return [('ApplicationName', stack.name)] + \
                   [(out.key, out.value)
                    for out in
                    self.describe(
                        stack.env + "-env").outputs
                    if
                    out.key in stack.inputs]

    def load_template_body(self, template):
        return cf.helpers.template_body(template)

    def validate(self, stack):
        return self.validator.validate(stack)

    def update_template_versions(self, version, stack):
        if version.startswith('ami-'):
            self.ec2_conn.get_image(version)
            cf.helpers.update_base_image_param(version, stack.template_body, stack.template)
        elif cf.helpers.check_docker_tag_exists(version, stack.name, HTTPSConnection(
                stack.config['repository']['index']), stack.config):
            cf.helpers.update_version_param(version, stack.template_body, stack.template)
        else:
            print(
                "Error: Cloud not find docker container {} with tag {}".format(stack.name,
                                                                               version))
            return False
        return True

    def lock(self, stack_name):
        return self.cf_conn.set_stack_policy(stack_name, self.__stack_policy('Deny'))

    def __stack_policy(self, effect):
        return """{
                  "Statement" : [
                    {
                      "Effect" : \""""+effect+"""\",
                      "Action" : "Update:*",
                      "Principal": "*",
                      "Resource" : "*"
                    }
                  ]
                }"""

    def unlock(self, stack_name):
        return self.cf_conn.set_stack_policy(stack_name, self.__stack_policy('Allow'))

    def describe(self, stack_name):
        print("Describing:", stack_name)
        return cf.helpers.describe_stack(self.cf_conn, stack_name)

    def delete(self, stack_name):
        print("Deleting:", stack_name)
        return self.cf_conn.delete_stack(stack_name)

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
