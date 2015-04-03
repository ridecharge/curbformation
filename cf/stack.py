import cf.helpers


class Stack(object):
    def __init__(self, service, options):
        self.service = service
        self.env = options.environment
        self.region = options.region
        self.name = options.name
        self.config = cf.helpers.config(self.env)
        self.account_id = self.config['AccountId']
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

    def sync(self):
        return self.service.sync_s3_bucket(self.bucket_name)

    def validate(self):
        return self.service.validate(self)

    def describe(self):
        return self.service.describe(self.stack_name)

    def delete(self):
        return self.service.delete(self.stack_name)

    def create(self):
        self.sync()
        return self.service.create(self)

    def update(self):
        self.sync()
        return self.service.update(self)

    def deploy(self):
        return self.service.deploy(self.options.version, self)


class StackService(object):
    def __init__(self, cf_conn, ec2_conn, validator, debug=False):
        self.cf_conn = cf_conn
        self.ec2_conn = ec2_conn
        self.validator = validator
        self.debug = debug

    def load_template_body(self, template):
        return cf.helpers.template_body(template)

    def params(self, stack):
        if stack.name == 'env':
            return [('Environment', stack.env)] + list(stack.config['env_params'].items())
        else:
            return [('ApplicationName', stack.name)] + [(out.key, out.value) for out in
                                                        self.describe(stack.env + "-env").outputs if
                                                        out.key in stack.inputs]

    def sync_s3_bucket(self, bucket_name):
        cf.helpers.sync_s3_bucket(bucket_name)

    def validate(self, stack):
        return self.validator.validate(stack)

    def deploy(self, version, stack):
        if cf.helpers.check_if_version_exists(version, stack.name):
            cf.helpers.update_version_param(version, stack.template_body, stack.template)
            return self.update(stack)
        else:
            print("Cloud not find docker container {} with tag {} for ".format(stack.name, version))
            return False

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
