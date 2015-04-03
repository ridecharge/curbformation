import json
import sys
import time
import os
from http.client import HTTPSConnection
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


def template_body(template, path="../curbformation-templates/"):
    with open(path + template) as f:
        return json.load(f)


def inputs(temp_body):
    return set(temp_body['Parameters'].keys())


def default_inputs(temp_body):
    return set(key for key, val in temp_body['Parameters'].items() if 'Default' in val)


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
    call(['aws', 's3', 'sync', '../curbformation-templates',
          's3://' + name, '--delete', '--exclude', '*', '--include', '*.json'])


def delete_s3_bucket_contents(name):
    call(['aws', 's3', 'rm', 's3://' + name, '--recursive'])


def templates_dir_exists():
    if not os.path.isdir('../curbformation'):
        print('The directory ../curbformation must exist to run this command')
        sys.exit(1)


def check_if_version_exists(version, name):
    cfg_path = os.path.expanduser("~") + "/.dockercfg"
    with open(cfg_path) as f:
        cfg = json.load(f)
        auth = cfg['https://index.docker.io/v1/']['auth']
        headers = {'Authorization': 'Basic %s' % auth}
    c = HTTPSConnection('index.docker.io')
    c.request('GET', "/v1/repositories/ridecharge/{}/tags/{}".format(name, version),
              headers=headers)
    resp = c.getresponse().read().decode("utf-8")
    return resp != 'Tag not found'


def update_version_param(version, template, path):
    print("Updating", path, "Version to", version)
    template['Parameters']['Version']['Default'] = version
    with open("../curbformation-templates/" + path, 'w') as of:
        json.dump(template, of, sort_keys=True, indent=2)


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
