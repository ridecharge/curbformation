import json


def topic_name(env):
    return "arn:aws:sns:us-east-1:563891166287:curbformation-{}-notifications".format(env)


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
    with open("../curbformation-templates/" + template) as f:
        return json.load(f)


def inputs(temp_body):
    return set(temp_body['Parameters'].keys())
