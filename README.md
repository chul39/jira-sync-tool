# Jira Board Synchronization Tool

An automated tool for keeping status synchronized across multiple Jira boards.

## How to Use

Imagine managing multiple Jira boards and needing to synchronize the status of related issues.

```text
               [ Publisher Board ] 
                 Issue: ABC-123 
              (Status: In Progress)
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
[ Subscriber A Board ]       [ Subscriber B Board ]
    Issue: DEF-456               Issue: GHI-789
    (Status: To-do)              (Status: To-do)
```

Instead of updating manually, simply add a tag to the issue description in your subscriber boards.

```text
[Sync-ID: ABC-123]
```

The tool will monitor the publisher board hourly, automatically syncing the status to all subscriber boards.

```text
               [ Publisher Board ] 
                 Issue: ABC-123 
              (Status: In Progress)
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
[ Subscriber A Board ]       [ Subscriber B Board ]
    Issue: DEF-456               Issue: GHI-789
 (Status: In Progress)        (Status: In Progress)
```

## Installation

### Prerequisites

* Python 3.x

### Steps

1. Clone the repository and navigate to the project root:

```bash
git clone https://github.com/chul39/jira-sync-tool
cd jira-sync-tool
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running Locally

1. Create a `.env` file at the root of the project:

```text
PUBLISHER_DATA={"domain": "https://publisher.atlassian.net", "project": "publisher-project-key", "email": "publisher@domain.com", "token": "publisher-api-token"}
SUBSCRIBER_DATA=[{"domain": "https://subscriber1.atlassian.net", "project": "subscriber1-project-key", "email": "subscriber1@domain.com", "token": "subscriber1-api-token"}, ...]
```

2. Execute the script:

```bash
python lambda_function.py
```

## Running on AWS

1. Create your Identity Provider in AWS with the following configuration:
* Set Provider URL to `https://token.actions.githubusercontent.com`
* Set Audience to `sts.amazonaws.com`

2. Create an IAM Role using the Identity Provider:
* Set the Trusted entity type to `Web identity`.
* Attach the following Permissions Policy:

```yaml
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFormationManagement",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResources",
        "cloudformation:GetTemplate",
        "cloudformation:UpdateStack",
        "cloudformation:CreateChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:ValidateTemplate",
        "cloudformation:GetTemplateSummary",
        "cloudformation:ListStacks"
      ],
      "Resource": [
        "arn:aws:cloudformation:ap-northeast-1:<YOUR_ACCOUNT_ID>:stack/jira-cross-domain-sync-stack/*",
        "arn:aws:cloudformation:ap-northeast-1:<YOUR_ACCOUNT_ID>:stack/aws-sam-cli-managed-default/*"
      ]
    },
    {
      "Sid": "TransformAndGlobal",
      "Effect": "Allow",
      "Action": "cloudformation:CreateChangeSet",
      "Resource": "arn:aws:cloudformation:ap-northeast-1:aws:transform/Serverless-2016-10-31"
    },
    {
      "Sid": "LambdaManagement",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:TagResource",
        "lambda:UntagResource"
      ],
      "Resource": "arn:aws:lambda:ap-northeast-1:<YOUR_ACCOUNT_ID>:function:jira-cross-domain-sync-*"
    },
    {
      "Sid": "EventBridgeManagement",
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:DeleteRule",
        "events:DescribeRule",
        "events:PutTargets",
        "events:RemoveTargets"
      ],
      "Resource": "arn:aws:events:ap-northeast-1:<YOUR_ACCOUNT_ID>:rule/jira-cross-domain-sync-*"
    },
    {
      "Sid": "S3StagingManagement",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::aws-sam-cli-managed-default-samclisourcebucket-*"
    },
    {
      "Sid": "IAMRoleAndPassRoleManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::<YOUR_ACCOUNT_ID>:role/jira-cross-domain-sync-*"
    },
    {
      "Sid": "LogGroupManagement",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups"
      ],
      "Resource": "arn:aws:logs:ap-northeast-1:<YOUR_ACCOUNT_ID>:log-group:/aws/lambda/jira-cross-domain-sync-*"
    }
  ]
}
```

3. Fork this repository and configure your GitHub Secrets:

* PUBLISHER_DATA: Same as your local .env
* SUBSCRIBER_DATA: Same as your local .env
* AWS_ROLE_TO_ASSUME: ARN of the IAM role

4. Trigger the deploy workflow and you are set!
