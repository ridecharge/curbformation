from cf import validation
from cf.stacks import service
from cf.stacks import environment
from cf.stacks import application


def new_stack_service(cf_conn, ec2_conn, route53_conn=None):
    stack_validator = validation.new_nested_stack_validator(cf_conn)
    return service.StackService(cf_conn, ec2_conn, route53_conn, stack_validator)


def new_bootstrap_service(ec2_conn, s3_conn, sns_conn):
    return service.BootstrapService(ec2_conn, s3_conn, sns_conn)


def new_environment_stack(cf_conn, ec2_conn, route53_conn, options):
    stack_service = new_stack_service(cf_conn, ec2_conn, route53_conn)
    return environment.Environment(stack_service, **options)


def new_bootstrap_environment(ec2_conn, s3_conn, sns_conn, options):
    bootstrap_service = new_bootstrap_service(ec2_conn, s3_conn, sns_conn)
    return environment.BootstrapEnvironment(bootstrap_service, **options)


def new_application_stack(cf_conn, ec2_conn, options):
    stack_service = new_stack_service(cf_conn, ec2_conn)
    return application.Application(stack_service, **options)

