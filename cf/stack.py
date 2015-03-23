import cf.helpers


class Stack(object):
    def __init__(self, service, **options):
        self.service = service
        self.env = options['environment']
        self.region = options['region']
        self.name = options['name']
        self.config = cf.helpers.config(self.env)
        self.accountId = self.config['AccountId']
        self.template = self.name + '.json'
        self.capabilities = ['CAPABILITY_IAM']
        self.bucket_name = cf.helpers.s3_bucket_name(self.env)
        self.stack_name = cf.helpers.stack_name(self.env, self.name)
        self.template_uri = cf.helpers.template_uri(self.bucket_name, self.template)
        self.template_body = cf.helpers.template_body(self.template)
        self.tags = cf.helpers.tags(self.env, self.template)
        self.inputs = cf.helpers.inputs(self.template_body)
        self.params = cf.helpers.params(self)
        self.topic_arn = cf.helpers.topic_arn(self.env, self.region, self.accountId)

    def validate(self):
        return self.service.validate(self)

    def describe(self):
        return self.service.describe(self)

    def delete(self):
        return self.service.delete(self)

    def create(self):
        return self.service.create(self)

    def update(self):
        return self.service.update(self)


class StackService(object):
    def __init__(self, cf_conn, ec2_conn, validator, debug=False):
        self.cf_conn = cf_conn
        self.ec2_conn = ec2_conn
        self.validator = validator
        self.debug = debug

    def validate(self, stack):
        return self.validator.validate(stack)

    def describe(self, stack):
        print("Describing:", stack.stack_name)
        return cf.helpers.describe_stack(self.cf_conn, stack.stack_name)

    def delete(self, stack):
        print("Deleting:", stack.stack_name)
        return self.cf_conn.delete_stack(stack.stack_name)

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
