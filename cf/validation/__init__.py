from cf.validation import validator


def new_nested_stack_validator(cf_conn):
    return validator.NestedStackValidator(cf_conn)

