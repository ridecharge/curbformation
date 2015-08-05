from cf.stack import Stack
from cf.stack import StackService
from cf.validator import NestedStackValidator
from cf.environment import Environment
from cf.environment import EnvironmentService
from boto import ec2
from boto import cloudformation
from boto import sns
from boto import s3
from consul import Consul


def new_environment(options):
    sns_conn = sns.connect_to_region(options.region)
    s3_conn = s3.connect_to_region(options.region)
    ec2_conn = ec2.connect_to_region(options.region)
    consul_conn = Consul(options.host, options.port)
    environment_service = EnvironmentService(ec2_conn, s3_conn, sns_conn, consul_conn)
    return Environment(environment_service, options)


def new_stack(options):
    consul_conn = Consul(options.host, options.port)
    cf_conn = cloudformation.connect_to_region(options.region)
    ec2_conn = ec2.connect_to_region(options.region)
    stack_validator = NestedStackValidator(cf_conn)
    stack_service = StackService(cf_conn, ec2_conn, consul_conn, stack_validator)
    return Stack(stack_service, options)

