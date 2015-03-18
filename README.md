# curbformation
This repository containers the python3 package for interactions with the CloudFormation AWS service.

## Development Env
To allow for easy development of this tool and cloudformation templates you'll want to setup you're environment like so.

1. Create and set a python3 pyenv virtualenv called curbformation
2. Run pip install -e . to install the package from the local folder to pickup changes
3. In the curbformation-templates folder set the virutalenv to the same curbformation as step 1.
4. Now you are ready to easily develop.

## Commands
* bootstrap - this command prepares an environment to be ready for use with CloudFormation.  
  * Creates a bootstrap deployment key
  * Creates a s3 bucket to hold cloudformation templates
  * Creates a SNS topic for cloudformation notifications
* cleanup - this command deletes the resources created by the boostrap command
* create - this command creates a top level template.  by default this is the env.json template but can use -n to set the template to use.
  * The template name is used along with the environment (default test -e env to set) to create the stack_name used by cloudformation and the ApplicationName parameter in the non env templates. 
  * Inputs to the non env templates will be queried from the outputs of the env template to provide consistency across the environment and apps.
* update - this command updates an existing stack to make changes reflected in the json templates. This will reuse the input the parameters for an env and non env templates will do the same as in create
* delete - this a deletes a stack, doing any dynamicly created resources first to allow for cloudformation templates to delete without failure.
* validate - this will do a various linting/validations on the templates before use.
  * will use aws validation to check basic template syntax
  * will do extra validation to check for nested stack inputs.  
  * currently does not check nested stack outputs referenced.