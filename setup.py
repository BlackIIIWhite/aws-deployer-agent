# setup.py (Corrected Version)
import boto3
import json
import time
import zipfile

# --- Configuration ---
AGENT_NAME = "CloudCraftAgent-Automated"
LAMBDA_FUNCTION_NAME = "CloudCraftActionGroup-Automated"
LAMBDA_ROLE_NAME = "CloudCraftLambdaRole-Automated"
AGENT_ROLE_NAME = "CloudCraftAgentRole-Automated"
REGION = "us-east-1"

# --- Agent Instructions ---
AGENT_INSTRUCTIONS = """
You are CloudCraft Agent, an expert AWS DevOps assistant. Your purpose is to help users deploy and manage AWS resources using natural language.
1. Analyze the user's request to understand their goal.
2. If you need more information (like an IAM role ARN, which you cannot create yourself), you MUST ask the user for it. Do not guess or make up values.
3. Create a multi-step plan to achieve the goal using the available tools.
4. The sequence of operations is critical. For a static website, the order must be: create_s3_bucket, disable_s3_block_public_access, set_public_read_policy, and then configure_s3_static_hosting.
"""


iam_client = boto3.client('iam', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
bedrock_agent_client = boto3.client('bedrock-agent', region_name=REGION)

def create_iam_role(role_name, trust_policy):
    """Creates an IAM role and returns its ARN."""
    try:
        response = iam_client.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy))
        return response['Role']['Arn']
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"Role '{role_name}' already exists. Fetching ARN.")
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']

def create_lambda_function(role_arn):
    """Packages and creates the Lambda function for the action group."""
    print("Zipping Lambda function code...")
    with zipfile.ZipFile('backend/lambda_function.zip', 'w') as z:
        z.write('backend/lambda_function.py', arcname='lambda_function.py')
    with open('backend/lambda_function.zip', 'rb') as f:
        zip_bytes = f.read()
    print(f"Creating Lambda function '{LAMBDA_FUNCTION_NAME}'...")
    try:
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME, Runtime='python3.12', Role=role_arn,
            Handler='lambda_function.lambda_handler', Code={'ZipFile': zip_bytes},
            Timeout=120, Publish=True,
        )
        return response['FunctionArn']
    except lambda_client.exceptions.ResourceConflictException:
        print(f"Lambda function '{LAMBDA_FUNCTION_NAME}' already exists. Skipping.")
        account_id = boto3.client('sts').get_caller_identity()['Account']
        return f"arn:aws:lambda:{REGION}:{account_id}:function:{LAMBDA_FUNCTION_NAME}"

def create_bedrock_agent(agent_role_arn, foundation_model, instruction):
    """Creates the Bedrock Agent shell."""
    print(f"Creating Bedrock Agent '{AGENT_NAME}'...")
    try:
        response = bedrock_agent_client.create_agent(
            agentName=AGENT_NAME,
            agentResourceRoleArn=agent_role_arn,
            foundationModel=foundation_model,
            instruction=instruction, # Instruction is now included
            idleSessionTTLInSeconds=600,
        )
        return response['agent']
    except bedrock_agent_client.exceptions.ConflictException:
        print(f"Agent '{AGENT_NAME}' already exists. Fetching details.")
        agents = bedrock_agent_client.list_agents()['agentSummaries']
        agent = next((a for a in agents if a['agentName'] == AGENT_NAME), None)
        return bedrock_agent_client.get_agent(agentId=agent['agentId'])['agent']

if __name__ == "__main__":
    print("--- Starting CloudCraft Agent Infrastructure Setup ---")
    
    # Steps 1 & 2: Create IAM roles
    print("\nStep 1: Creating IAM Role for Lambda...")
    lambda_trust_policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    lambda_role_arn = create_iam_role(LAMBDA_ROLE_NAME, lambda_trust_policy)
    iam_client.attach_role_policy(RoleName=LAMBDA_ROLE_NAME, PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess')
    iam_client.attach_role_policy(RoleName=LAMBDA_ROLE_NAME, PolicyArn='arn:aws:iam::aws:policy/AWSLambda_FullAccess')
    iam_client.attach_role_policy(RoleName=LAMBDA_ROLE_NAME, PolicyArn='arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator')
    print(f"Lambda Role ARN: {lambda_role_arn}")

    print("\nStep 2: Creating IAM Role for Bedrock Agent...")
    agent_trust_policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "bedrock.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    agent_role_arn = create_iam_role(AGENT_ROLE_NAME, agent_trust_policy)
    iam_client.put_role_policy(
        RoleName=AGENT_ROLE_NAME, PolicyName='AllowClaude3SonnetInvoke',
        PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": f"arn:aws:bedrock:{REGION}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"}]})
    )
    print(f"Agent Role ARN: {agent_role_arn}")

    print("Waiting 10 seconds for IAM roles to propagate...")
    time.sleep(10)
    
    # Step 3: Create Lambda Function
    print("\nStep 3: Creating Lambda Function...")
    lambda_arn = create_lambda_function(lambda_role_arn)
    print(f"Lambda Function ARN: {lambda_arn}")

    # Step 4: Create the Bedrock Agent (now with instructions)
    print("\nStep 4: Creating the Bedrock Agent...")
    agent_details = create_bedrock_agent(agent_role_arn, "anthropic.claude-3-sonnet-20240229-v1:0", AGENT_INSTRUCTIONS)
    agent_id = agent_details['agentId']
    print(f"Agent created with ID: {agent_id}")

    # Waiter loop
    print("Waiting for agent to be created...")
    while True:
        get_agent_response = bedrock_agent_client.get_agent(agentId=agent_id)
        agent_status = get_agent_response['agent']['agentStatus']
        print(f"Current agent status: {agent_status}")
        if agent_status != 'CREATING':
            break
        time.sleep(10)
    
    # Step 5: Define and create Action Group in Code
    print("\nStep 5: Creating the Agent Action Group...")
    try:
        bedrock_agent_client.create_agent_action_group(
            agentId=agent_id, agentVersion='DRAFT', actionGroupName='CloudCraftTools',
            actionGroupExecutor={'lambda': lambda_arn},
            functionSchema={'functions': [
                {'name': 'create_s3_bucket', 'description': 'Creates a new Amazon S3 bucket.', 'parameters': {
                    'bucket_name': {'description': 'Globally unique name for the bucket.', 'type': 'string', 'required': True},
                    'region': {'description': 'The AWS region, e.g., us-east-1.', 'type': 'string', 'required': True}}},
                {'name': 'disable_s3_block_public_access', 'description': 'Disables block public access on an S3 bucket.', 'parameters': {
                    'bucket_name': {'description': 'Name of the S3 bucket.', 'type': 'string', 'required': True}}},
                {'name': 'set_public_read_policy', 'description': 'Applies a public read-only policy to an S3 bucket.', 'parameters': {
                    'bucket_name': {'description': 'Name of the S3 bucket.', 'type': 'string', 'required': True}}},
                {'name': 'configure_s3_static_hosting', 'description': 'Enables static website hosting on a bucket.', 'parameters': {
                    'bucket_name': {'description': 'Name of the S3 bucket.', 'type': 'string', 'required': True}}},
                {'name': 'create_hello_world_lambda', 'description': "Creates a simple 'Hello World' Lambda function.", 'parameters': {
                    'function_name': {'description': 'The name for the new Lambda function.', 'type': 'string', 'required': True},
                    'role_arn': {'description': 'The ARN of the IAM role for the Lambda to assume.', 'type': 'string', 'required': True}}}
            ]}
        )
        print("Action Group created successfully.")
    except bedrock_agent_client.exceptions.ConflictException:
        print("Action Group 'CloudCraftTools' already exists. Skipping creation.")

    # Step 6: Prepare the Agent
    print("\nStep 6: Preparing the Agent...")
    bedrock_agent_client.prepare_agent(agentId=agent_id)
    print("Agent preparation started.")
    
    # Wait for preparation
    while True:
        get_agent_response = bedrock_agent_client.get_agent(agentId=agent_id)
        agent_status = get_agent_response['agent']['agentStatus']
        print(f"Current agent status: {agent_status}")
        if agent_status == 'PREPARED':
            break
        time.sleep(10)

    # Step 7: Create an Alias
    print("\nStep 7: Creating Agent Alias...")
    try:
        alias_response = bedrock_agent_client.create_agent_alias(agentId=agent_id, agentAliasName='TestAlias')
        alias_id = alias_response['agentAlias']['agentAliasId']
        print(f"Alias 'TestAlias' created with ID: {alias_id}")
    except bedrock_agent_client.exceptions.ConflictException:
        print("Alias 'TestAlias' already exists. Fetching ID.")
        aliases = bedrock_agent_client.list_agent_aliases(agentId=agent_id)['agentAliasSummaries']
        alias = next((a for a in aliases if a['agentAliasName'] == 'TestAlias'), None)
        alias_id = alias['agentAliasId']

    print("\n--- Setup Complete! ---")
    print("Please use the following values in your backend/app.py file:")
    print(f'AGENT_ID = "{agent_id}"')
    print(f'AGENT_ALIAS_ID = "{alias_id}"')
    print("---------------------------------")