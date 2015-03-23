from cf.stack import Stack
from cf.stack import StackService
from cf.validator import NestedStackValidator
from cf.environment import Environment
from cf.environment import EnvironmentService


def new_environment(ec2_conn, s3_conn, sns_conn, options):
    environment_service = EnvironmentService(ec2_conn, s3_conn, sns_conn)
    return Environment(environment_service, **options)


def new_stack(cf_conn, ec2_conn, options):
    stack_validator = NestedStackValidator(cf_conn)
    stack_service = StackService(cf_conn, ec2_conn, stack_validator)
    return Stack(stack_service, **options)

