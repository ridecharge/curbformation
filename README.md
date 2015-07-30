# curbformation
This repository containers the python3 package for interactions with the CloudFormation AWS service.

## Commands
* bootstrap - this command prepares an environment to be ready for use with CloudFormation.  
  * Creates a bootstrap deployment key
  * Creates a s3 bucket to hold cloudformation templates
  * Creates a SNS topic for cloudformation notifications
* cleanup - this command deletes the resources created by the boostrap command
* create - this command creates a stack from a top level template. 
  * The template name is used along with the environment (default test -e env to set) to create the stack_name used by cloudformation and the ApplicationName parameter in the non env templates. 
  * Inputs to the non env templates will be queried from the outputs of the env template to provide consistency across the environment and apps.
* deploy - initiates a rolling update by changing the version parameter to a stack. 
  * ab deployments - if a template contains the DeployedAsg and Deploying parameters.
    * --commit commits to a deployment
    * --rolleback rolls back a deployment
* delete - this a deletes a stack
* validate - this will do a various linting/validations on the templates before use.
  * will use aws validation to check basic template syntax
  * will do extra validation to check for nested stack inputs.  
  * currently does not check nested stack outputs referenced.

 ## Top Level Templates
 A top level template is considered to be any template in the ../curbformation-templates folder from where this command is executed.

 Typically a top level template will be formed entirely from nested templates which will then be formed of other amazon resources.