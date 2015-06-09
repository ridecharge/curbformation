import cf.helpers


class Stack(object):
    VALID_DEPLOYMENT_STATES = ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE',
                               'ROLLBACK_COMPLETE']

    def __init__(self, service, options):
        self.service = service
        self.region = options.region
        self.name = options.name
        self.config = self.service.load_config()
        self.env = self.config['environment']
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
        self.description = None

    def validate(self):
        return self.service.validate(self)

    def describe(self):
        if not self.description:
            self.description = self.service.describe(self.stack_name)
        return self.description

    def delete(self):
        return self.service.delete(self.stack_name)

    def create(self):
        version = self.options.version
        cf.helpers.exit_when_invalid(self)
        cf.helpers.sync_s3_bucket(self.bucket_name)
        if version:
            self.service.update_version_params(version, version,
                                               self)
        return self.service.create(self)

    def is_deployable(self):
        return self.describe().stack_status in Stack.VALID_DEPLOYMENT_STATES

    def deploy(self):
        cf.helpers.exit_when_not_deployable(self)
        cf.helpers.exit_when_invalid(self)

        if self.name == 'env':
            return self.service.update(self)

        is_ab_deploying = cf.helpers.is_ab_deploying(self)
        if is_ab_deploying:
            cf.helpers.update_ab_deploy_params(self)

        if cf.helpers.deploying(self):
            version = cf.helpers.version(self)
            previous_version = cf.helpers.previous_version(self)
        elif self.options.version:
            version = self.options.version
            previous_version = cf.helpers.version(self)
        else:
            version = cf.helpers.version(self)
            previous_version = version
        self.service.update_version_params(version, previous_version, self)

        if not is_ab_deploying and previous_version == version:
            cf.helpers.add_serial_param(self.params)

        cf.helpers.sync_s3_bucket(self.bucket_name)
        return self.service.update(self)

    def lock(self):
        return self.service.lock(self.stack_name)

    def unlock(self):
        return self.service.unlock(self.stack_name)


class StackService(object):
    def __init__(self, cf_conn, ec2_conn, consul_conn, validator, debug=False):
        self.cf_conn = cf_conn
        self.ec2_conn = ec2_conn
        self.consul_conn = consul_conn
        self.validator = validator
        self.debug = debug

    def load_config(self):
        return cf.helpers.load_config(self.consul_conn)

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

    def update_version_params(self, version, previous_version, stack):
        if not stack.options.skip_version_check:
            cf.helpers.exit_when_version_not_found(version, stack, self.ec2_conn)
        cf.helpers.add_version_param(version, previous_version, stack.params)

    def lock(self, stack_name):
        return self.cf_conn.set_stack_policy(stack_name, self.__stack_policy('Deny'))

    def __stack_policy(self, effect):
        return """{
              "Statement" : [
                {
                  "Effect" : \"""" + effect + """\",
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
