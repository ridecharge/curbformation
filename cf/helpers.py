import json
import os
import time
from boto import cloudformation
from subprocess import call


def config(env):
    config_path = os.path.expanduser("~") + "/.cf/" + env + ".json"
    print("Using config:", config_path)
    with open(config_path, 'r') as f:
        return json.load(f)


def topic_name(env):
    return "curbformation-{}-notifications".format(env)


def describe_stack(cf_conn, name):
    return cf_conn.describe_stacks(name)[0]


def topic_arn(env, region, account_id):
    return ":".join(["arn:aws:sns", region, account_id, topic_name(env)])


def stack_name(env, name):
    return "{}-{}".format(env, name)


def s3_bucket_name(env):
    return "curbformation-{}-templates".format(env)


def template_uri(bucket_name, template):
    return "https://s3.amazonaws.com/" + bucket_name + "/" + template


def tags(env, template):
    return {
        'Environment': env,
        'Template': template
    }


def template_body(template):
    try:
        with open('../curbformation-templates/' + template) as f:
            return json.load(f)
    except FileNotFoundError:
        with open('../curbformation-templates-private/' + template) as f:
            return json.load(f)


def inputs(temp_body):
    return set(temp_body['Parameters'].keys())


def default_inputs(temp_body):
    return set(key for key, val in temp_body['Parameters'].items() if 'Default' in val)


def previous_version(stack):
    return 'ami-982727f0'
    for out in stack.describe().outputs:
        if out.key == 'PreviousVersion':
            return out.value
    print('Error: Could not find PreviousVersion')
    exit(1)


def version(stack):
    for out in stack.describe().outputs:
        if out.key == 'Version':
            return out.value
    print('Error: Could not find Version')
    exit(1)


def nested_stack_resources(temp_body):
    return [val for val in temp_body['Resources'].values() if
            val['Type'] == 'AWS::CloudFormation::Stack']


def nested_stack_dependencies(temp_body):
    dependencies = {}
    for resource in nested_stack_resources(temp_body):
        properties = resource['Properties']
        template_url = properties['TemplateURL']['Fn::Join'][1][-1]
        dependencies[template_url] = inputs(properties)
    return dependencies.items()


def sync_s3_bucket(name):
    __sync_s3_bucket(name, '../curbformation-templates')
    __sync_s3_bucket(name, '../curbformation-templates-private')


def __sync_s3_bucket(name, templates_path):
    call(['aws', 's3', 'sync', templates_path,
          's3://' + name, '--exclude', '*', '--include', '*.json'])


def delete_s3_bucket_contents(name):
    call(['aws', 's3', 'rm', 's3://' + name, '--recursive'])


def exit_when_invalid(stack):
    if not stack.validate():
        print("Error: Template Validation Failed")
        exit(1)


def exit_when_not_deployable(stack):
    if not stack.is_deployable():
        print('The current stack is in progress of updating and cannot be deployed.')
        exit(1)


def dockerhub_config():
    config_path = os.path.expanduser("~") + "/.dockercfg"
    print("Using dockercfg:", config_path)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def exit_if_docker_tag_not_exist(vers, name, https_conn, cfg):
    dh_config = dockerhub_config()
    headers = {}
    if dh_config:
        headers = {
            'Authorization': "Basic {}".format(
                dh_config["https://" + cfg['repository']['index'] + "/v1/"]['auth'])}
    https_conn.request('GET', cfg['repository']['tag_path'].format(name, version),
                       headers=headers)
    if https_conn.getresponse().read().decode('utf-8') != 'Tag not found':
        print(
            "Error: Could not find docker container {} with tag {}".format(name,
                                                                           vers))
        exit(1)


def add_serial_param(params):
    params.append(('Serial', str(int(time.time()))))


def add_version_param(vers, previous_vers, params):
    print("Updating Version to", vers)
    if not vers or not previous_vers:
        print("Error: Missing values vers:", vers, "previous_vers:", previous_vers)
        exit(1)
    params.append(('Version', vers))
    params.append(('PreviousVersion', previous_vers))


def describe_nested_stacks(name, region):
    cf_conn = cloudformation.connect_to_region(region)
    stack = describe_stack_resource(cf_conn, name)
    print(stack.outputs)
    print(stack.parameters)
    print(stack.stack_status)


def describe_stack_resource(cf_conn, name):
    stack = describe_stack(cf_conn, name)
    for resource in stack.list_resources():
        if resource.resource_type == 'AWS::CloudFormation::Stack':
            time.sleep(1)
            describe_stack_resource(cf_conn, resource.physical_resource_id)
        print(resource.logical_resource_id)
        print(resource.physical_resource_id)
        print(resource.resource_type)
        print(resource.resource_status)
        print(resource.resource_status_reason)
    return stack
