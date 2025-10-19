# backend/lambda_function.py (NEW VERSION)
import json
import boto3
import base64

# Initialize clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# --- Tool Functions (No changes to these) ---
def create_s3_bucket(bucket_name, region="us-east-1"):
    try:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            location_config = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location_config)
        return f"Success: Bucket '{bucket_name}' created in region {region}."
    except Exception as e:
        return f"Error: Failed to create bucket '{bucket_name}'. Reason: {str(e)}"

def disable_s3_block_public_access(bucket_name):
    try:
        s3_client.delete_public_access_block(Bucket=bucket_name)
        return f"Success: Disabled Block Public Access for '{bucket_name}'."
    except Exception as e:
        return f"Error: Failed to disable Block Public Access. Reason: {str(e)}"

def set_public_read_policy(bucket_name):
    try:
        policy = { "Version": "2012-10-17", "Statement": [{"Sid": "PublicReadGetObject", "Effect": "Allow", "Principal": "*", "Action": ["s3:GetObject"], "Resource": f"arn:aws:s3:::{bucket_name}/*"}]}
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        return f"Success: Set public read policy on '{bucket_name}'."
    except Exception as e:
        return f"Error: Failed to set bucket policy. Reason: {str(e)}"

def configure_s3_static_hosting(bucket_name):
    try:
        website_configuration = {'IndexDocument': {'Suffix': 'index.html'}}
        s3_client.put_bucket_website(Bucket=bucket_name, WebsiteConfiguration=website_configuration)
        return f"Success: Configured static hosting for '{bucket_name}'."
    except Exception as e:
        return f"Error: Failed to configure hosting. Reason: {str(e)}"

import base64 # Make sure base64 is imported at the top

def create_hello_world_lambda(function_name, role_arn):
    """Creates a simple 'Hello World' Lambda function using boto3."""
    try:
        # Dummy "hello world" Python code zip content (replace with real packaging if needed)
        zip_content = b'UEsDBBQAAAAIAAAAAAAAAAAAAAAAAAAAAAAACgAAAGxhbWJkYS5weVVUCQAD42iPZONoj2R1eAsAAQT1AQAABBQAAAAKAFBLAwQUAAAACAAzRj9XAAAAAAAAAAAAAAAACgAAAGxhbWJkYS5weVVUCQAD42iPZONoj2R1eAsAAQT1AQAABBQAAABNj8EKwjAQRO/5ij1L8CBFwaYPELyJ3sU2bJNJpdbS37fK6OHh5eHlIcyjsyhzg+bH4Y6xG7pM4LwzBwzD4R4s65lFQRBwL+M8kYTnyMgt43A3w4JvRT45PArvYxK2KZbI2hM2i5n8SL7k4Z28v/Xz/T8AAAD//wMAUEsBAi0AFAAAAAgAAAAAAAAAAAAAAAAAAAAAAAoAAAAAAAAAAAAAAL8AAAAAbGFtYmRhLnB5VVQJAAOjaI9k42iPZHV4CwABBPQBAAAEFAAAAABQSwECLQAUAAAACAAzRj9XAAAAAAAAAAAAAAAACgAAAAAAAAAAAAAAnwAAAGxhbWJkYS5weVVUCQAD42iPZONoj2R1eAsAAQT1AQAABBQAAAAAUEsFBgAAAAACAAIAfgAAAIgAAAAAAA=='
        zip_file = base64.b64decode(zip_content)

        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.12', # Or your preferred runtime
            Role=role_arn,
            Handler='lambda.lambda_handler', # Assumes the handler file is lambda.py and function is lambda_handler
            Code={'ZipFile': zip_file},
            Publish=True
        )
        return f"Success: Lambda function '{function_name}' created. ARN: {response['FunctionArn']}"
    except lambda_client.exceptions.ResourceConflictException:
        return f"Error: Lambda function '{function_name}' already exists."
    except Exception as e:
        return f"Error: Failed to create Lambda function '{function_name}'. Reason: {str(e)}"

# --- Main Handler (CRITICAL UPDATE HERE) ---
def lambda_handler(event, context):
    # This new event format is simpler
    function_name = event['function']
    parameters_list = event.get('parameters', [])
    
    # Convert the list of parameters into a simple dictionary
    args = {param['name']: param['value'] for param in parameters_list}
    
    print(f"Invoked function: {function_name} with arguments: {args}")

    response_body = ""
    # Determine which function to call based on the function name
    if function_name == 'create_s3_bucket':
        response_body = create_s3_bucket(**args)
    elif function_name == 'disable_s3_block_public_access':
        response_body = disable_s3_block_public_access(**args)
    elif function_name == 'set_public_read_policy':
        response_body = set_public_read_policy(**args)
    elif function_name == 'configure_s3_static_hosting':
        response_body = configure_s3_static_hosting(**args)
    elif function_name == 'create_hello_world_lambda':
        response_body = create_hello_world_lambda(**args)
    else:
        response_body = f"Error: Unknown function '{function_name}'"

    # This is the response format Bedrock expects for this method
    response = {
        'response': {
            'actionGroup': event['actionGroup'],
            'function': event['function'],
            'functionResponse': {
                'responseBody': {
                    'TEXT': {'body': response_body}
                }
            }
        },
        'messageVersion': event['messageVersion']
    }
    
    return response