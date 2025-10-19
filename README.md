# 🤖 CloudCraft Agent: Your Conversational AWS DevOps Assistant

**Elevator Pitch:** An autonomous DevOps assistant that builds and deploys serverless applications and static websites on AWS from simple, conversational prompts. 🚀

---

## 📖 About The Project

CloudCraft Agent leverages the power of Amazon Bedrock Agents to understand natural language commands and automate cloud infrastructure tasks. Instead of complex manual configurations in the AWS console or writing intricate Infrastructure as Code templates, you can simply chat with the agent to deploy resources like S3 static websites or basic Lambda functions.

This project was built for the **AWS AI Agent Global Hackathon**, demonstrating how generative AI can simplify complex cloud operations.



---

## ✨ Features

* **Conversational Deployment:** Use natural language to deploy AWS resources.
* **Automated Infrastructure Setup:** A Python script (`setup.py`) provisions the necessary IAM roles, Lambda function, and Bedrock Agent.
* **S3 Static Website Deployment:** Creates, configures (including public access), and prepares S3 buckets for static website hosting.
* **File Upload Integration:** After bucket creation, the frontend allows direct upload of website files via the local backend.
* **Basic Lambda Creation:** Capable of creating simple "Hello World" Lambda functions (requires providing an execution role ARN).
* **Serverless Architecture:** Built primarily using Amazon Bedrock Agents and AWS Lambda for scalability and cost-efficiency.

---

## 🛠️ Tech Stack

* **Cloud Platform:** AWS
* **Core AI Service:** Amazon Bedrock (Agents for Bedrock, Anthropic Claude 3 Sonnet)
* **Compute:** AWS Lambda
* **Identity & Access Management:** AWS IAM
* **Backend:** Python, Flask, Boto3
* **Frontend:** HTML, CSS, JavaScript

---

## ✅ Prerequisites

1.  **AWS Account:** You need an active AWS account.
2.  **IAM User with Admin Privileges:** Create an IAM user in your AWS account and attach the `AdministratorAccess` managed policy. This is required to run the `setup.py` script which creates other roles and resources.
3.  **AWS CLI Configured:** Install the [AWS CLI](https://aws.amazon.com/cli/) and configure it with the credentials for the admin IAM user created above. Run `aws configure` in your terminal and provide the Access Key ID, Secret Access Key, and default region (e.g., `us-east-1`). Verify with `aws sts get-caller-identity`.
4.  **Python 3.8+:** Ensure you have Python installed.
5.  **Git:** Required for cloning the repository.

---

## 🚀 Setup and Running Instructions

Follow these steps precisely to set up and run the CloudCraft Agent:

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/BlackIIIWhite/aws-deployer-agent.git](https://github.com/BlackIIIWhite/aws-deployer-agent.git)
    cd aws-deployer-agent
    ```

2.  **Set Up Python Environment & Dependencies:**
    ```bash
    # Create a virtual environment (optional but recommended)
    python -m venv my_env

    # Activate it
    # Windows:
    .\my_env\Scripts\activate
    # macOS/Linux:
    source my_env/bin/activate

    # Install required packages
    pip install -r backend/requirements.txt
    ```

3.  **Request Anthropic Model Access (CRITICAL ONE-TIME STEP):**
    * Navigate to the **Amazon Bedrock** console in your AWS account.
    * Go to **Model catalog** (under "Discover").
    * Find and click on **Claude 3 Sonnet**.
    * Click **"Request model access"** or **"Submit use case details"**.
    * Fill out the form (you can use your name for the company, GitHub URL for the website, and describe the project as "Building a DevOps agent for the AWS Hackathon").
    * **Wait for confirmation** that access is granted (usually quick).

4.  **Run the Infrastructure Setup Script:**
    This script creates the IAM roles, Lambda function, and Bedrock Agent. Ensure your AWS CLI is configured with admin credentials before running.
    ```bash
    python setup.py
    ```
    *Wait for the script to complete.* It will print the `AGENT_ID` and `AGENT_ALIAS_ID` at the end. Copy these values.

## ⚠️ Troubleshooting: Fixing Lambda Invoke Permissions 
You might encounter an Access denied while invoking Lambda function... error if the automated permission setup in setup.py didn't fully propagate or failed silently. If this happens, you need to manually add a resource-based policy to your Lambda function:
## 1.  Find your Agent ARN:
* Go to the Amazon Bedrock console -> Agents.
* Click on your agent (CloudCraftAgent-Automated).
* On the Agent overview page, copy the Agent ARN (it looks like arn:aws:bedrock:<region>:<account_id>:agent/<agent_id>).
* Go to your Lambda Function:
* Navigate to the AWS Lambda console -> Functions.
* Click on CloudCraftActionGroup-Automated.

## 2.  Add Permission:
* Click the Configuration tab, then select Permissions on the left.
* Scroll down to the Resource-based policy section and click Add permissions.
* Select AWS Service as the trigger type.

## 3.  Configure the statement:
* Service principal: Choose Bedrock from the dropdown (bedrock.amazonaws.com).
* Statement ID: Enter a unique name, like AllowBedrockAgentInvoke-Manual.
* Source ARN: Paste the Agent ARN you copied in step 1.
* Action: Select lambda:InvokeFunction.
* Click Save.
## Prepare Agent: Go back to your agent in the Bedrock console, click "Test," then click "Prepare" one last time.


5.  **Configure the Backend:**
    * Open the `backend/app.py` file in a text editor.
    * Paste the `AGENT_ID` and `AGENT_ALIAS_ID` you copied into the placeholder variables at the top of the file.
    * Save the file.

6.  **Run the Backend Server:**
    Make sure you are in the project's root directory (`aws-deployer-agent`).
    ```bash
    python -m backend.app
    ```
    Leave this terminal running. It's your active backend.

7.  **Launch the Frontend:**
    * Using your computer's file explorer, navigate to the `frontend` folder.
    * Double-click the `index.html` file to open it in your web browser (Chrome recommended).

---

## ▶️ Usage Example

1.  The CloudCraft Agent chat interface will appear.
2.  In the text box, enter a prompt like:
    `Deploy a new static website named my-hackathon-blog.`
3.  Click "Send Message".
4.  The agent will process the request and respond in the "Conversation Log". If it successfully creates the S3 bucket, it will list the steps performed.
5.  If bucket creation is successful, an **"Upload Website Files"** section will appear below the chat log, showing the target bucket name.
6.  Click "Choose Files", select your website files (e.g., `index.html`, `style.css`), and click the "Upload Files" button.
7.  The status message will indicate if the upload was successful.
8.  You can then find the public URL for your website in the AWS S3 console (Bucket -> Properties -> Static website hosting endpoint).

---

## ⚠️ Important Notes & Troubleshooting

* **Permissions:** The `setup.py` script requires administrator privileges on your AWS account to create resources. The Flask backend (`app.py`) runs with the credentials you configured via `aws configure`, which needs `bedrock:InvokeAgent` permission for the specific agent alias.
* **Lambda Permissions Error:** If you encounter an `Access denied while invoking Lambda function...` error after the agent creates the bucket, it means the automatic permission setup in `setup.py` might have failed. You may need to manually add a resource-based policy to the `CloudCraftActionGroup-Automated` Lambda function, allowing the `bedrock.amazonaws.com` principal to `lambda:InvokeFunction`, conditioned on your specific Agent ARN (`AWS:SourceArn`).
* **Clean Up:** Remember to **delete the AWS resources** created by `setup.py` (Bedrock Agent, Lambda function, IAM roles, S3 bucket) from the AWS Console when you are finished to avoid potential costs.

---
