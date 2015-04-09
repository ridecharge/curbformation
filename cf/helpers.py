import json
import time
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


def template_body(template, path="../curbformation-templates/"):
    with open(path + template) as f:
        return json.load(f)


def inputs(temp_body):
    return set(temp_body['Parameters'].keys())


def default_inputs(temp_body):
    return set(key for key, val in temp_body['Parameters'].items() if 'Default' in val)


def previous_version(temp_body):
    try:
        return temp_body['Parameters']['PreviousVersion']['Default']
    except KeyError:
        try:
            return temp_body['Parameters']['PreviousImageId']['Default']
        except KeyError:
            print('Error: Cloud not find Default Previous Version or Default ImageId parameters')
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
    call(['aws', 's3', 'sync', '../curbformation-templates',
          's3://' + name, '--delete', '--exclude', '*', '--include', '*.json'])


def delete_s3_bucket_contents(name):
    call(['aws', 's3', 'rm', 's3://' + name, '--recursive'])


def templates_dir_exists():
    if not os.path.isdir('../curbformation'):
        print('The directory ../curbformation must exist to run this command')
        exit(1)


def dockerhub_config():
    config_path = os.path.expanduser("~") + "/.dockercfg"
    print("Using dockercfg:", config_path)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def check_docker_tag_exists(version, name, https_conn, cfg):
    dh_config = dockerhub_config()
    headers = {}
    if dh_config:
        headers = {
            'Authorization': "Basic {}".format(
                dh_config["https://" + cfg['repository']['index'] + "/v1/"]['auth'])}
    https_conn.request('GET', cfg['repository']['tag_path'].format(name, version),
                       headers=headers)
    return https_conn.getresponse().read().decode('utf-8') != 'Tag not found'


def update_serial_param(template, path):
    try:
        template['Parameters']['Serial']['Default'] = str(int(time.time()))
    except KeyError:
        print('Error: This template does not have a default Serial parameter.')
        exit(1)
    with open("../curbformation-templates/" + path, 'w') as of:
        json.dump(template, of, sort_keys=True, indent=2)


def update_version_param(version, template, path):
    print("Updating", path, "Version to", version)
    try:
        prev_version = template['Parameters']['Version']['Default']
        template['Parameters']['Version']['Default'] = version
        template['Parameters']['PreviousVersion']['Default'] = prev_version
    except KeyError:
        print("Error: This template does not have a Default Version parameter.")
        exit(1)
    with open("../curbformation-templates/" + path, 'w') as of:
        json.dump(template, of, sort_keys=True, indent=2)


def update_base_image_param(image_id, template, path):
    print("Updating", path, "ImageId to", image_id)
    try:
        prev_image_id = template['Parameters']['ImageId']['Default']
        template['Parameters']['ImageId']['Default'] = image_id
        template['Parameters']['PreviousImageId']['Default'] = prev_image_id
    except KeyError:
        print("Error: This template does not have a Default ImageId parameter.")
        exit(1)
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
