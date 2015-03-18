import json
from subprocess import call
from os.path import expanduser


class StackService(object):
    def __init__(self, cf_conn, ec2_conn, route53_conn, validator, debug=False,
                 namespace='curbformation'):
        self.cf_conn = cf_conn
        self.ec2_conn = ec2_conn
        self.route53_conn = route53_conn
        self.validator = validator
        self.debug = debug
        self.namespace = namespace

    def build_topic_name(self, stack):
        return 'arn:aws:sns:us-east-1:563891166287:' + build_topic_name(stack.env, self.namespace)

    def build_stack_name(self, stack):
        return "-".join(["{0.env}", "{0.name}"]).format(stack)

    def build_s3_bucket_name(self, bootstrap):
        return build_bucket_name(bootstrap.env, self.namespace)

    def build_template_uri(self, stack):
        return "https://s3.amazonaws.com/" + stack.bucket_name + "/" + stack.template

    def build_tags(self, stack):
        return {
            'Environment': stack.env,
            'Template': stack.template
        }

    def load_template_body(self, stack):
        with open("../"+self.namespace+"-templates/"+stack.template) as f:
            return json.load(f)

    def build_inputs(self, stack):
        return set(stack.template_body['Parameters'].keys())

    def build_params(self, stack):
        # All stacks have the environment param, and
        # stacks with more inputs will call out and get them
        # from the environment stack
        params = [('Environment', stack.env)]
        if stack.name == 'env':
            return params + self.__read_config(stack)
        else:
            if 'ApplicationName' in stack.inputs:
                params.append(('ApplicationName', stack.name))
            return params + [(out.key, out.value) for out in
                             self.__describe(stack.env + '-env').outputs if
                             out.key in stack.inputs]

    def __read_config(self, stack):
        config_path = expanduser("~") + "/.cf/" + stack.env + ".json"
        print("Using config:", config_path)
        with open(config_path, 'r') as f:
            return list(json.load(f).items())

    def delete_dynamic_record_sets(self, stack):
        zone = self.route53_conn.get_zone(stack.public_internal_domain)
        for record in zone.get_records():
            if record.type not in ['NS', 'SOA']:
                print("Deleting record", record.name)
                zone.delete_record(record)

    def validate(self, stack):
        return self.validator.validate(stack)

    def __describe(self, stack_name):
        return self.cf_conn.describe_stacks(stack_name)[0]

    def describe(self, stack):
        print("Describing:", stack.stack_name)
        return self.__describe(stack.stack_name)

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
            notification_arns=stack.topic_name
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
            notification_arns=stack.topic_name
        )


def build_topic_name(environment, namespace):
    return "{}-{}-notifications".format(namespace, environment)


def build_bucket_name(environment, namespace):
    return "{}-{}-templates".format(namespace, environment)


class BootstrapService(object):
    def __init__(self, ec2_conn, s3_conn, sns_conn, namespace='curbformation'):
        self.ec2_conn = ec2_conn
        self.s3_conn = s3_conn
        self.sns_conn = sns_conn
        self.namespace = namespace

    def build_s3_bucket_name(self, bootstrap):
        return build_bucket_name(bootstrap.env, self.namespace)

    def build_topic_name(self, bootstrap):
        return build_topic_name(bootstrap.env, self.namespace)

    def create_s3_bucket(self, bootstrap):
        print("Creating S3 Bucket:", bootstrap.bucket_name)
        self.s3_conn.create_bucket(bootstrap.bucket_name)

    def delete_s3_bucket(self, bootstrap):
        print("Deleting S3 Bucket and contents:", bootstrap.bucket_name)
        call(['aws', 's3', 'rm', 's3://' + bootstrap.bucket_name, '--recursive'])
        self.s3_conn.delete_bucket(bootstrap.bucket_name)

    def create_sns_topics(self, bootstrap):
        print("Creating SNS Topic:", bootstrap.topic_name)
        self.sns_conn.create_topic(bootstrap.topic_name)

    def delete_sns_topic(self, bootstrap):
        print("Deleting SNS Topic:", bootstrap.topic_name)
        self.sns_conn.delete_topic('arn:aws:sns:us-east-1:563891166287:' + bootstrap.topic_name)

    def create_key_pair(self, bootstrap):
        print("Creating key pair:", bootstrap.env)
        try:
            self.ec2_conn.create_key_pair(bootstrap.env)
        except:
            print("Key pair exists skipping.")

    def delete_key_pair(self, bootstrap):
        print("Deleting key pair:", bootstrap.env)
        self.ec2_conn.delete_key_pair(bootstrap.env)

    def sync_s3_bucket(self, bootstrap):
        call(['aws', 's3', 'sync', '../{}-templates'.format(self.namespace),
              's3://' + bootstrap.bucket_name, '--delete', '--exclude', '*', '--include', '*.json'])

