AIMatic EC2 Deployment Stack - README
======================================

Prerequisites:
--------------
  • AWS account with permissions to create VPC, Subnets, EC2, Security Groups, IAM roles, and Elastic IP.
  • Access to AWS CloudFormation console or AWS CLI.
  • An existing EC2 Key Pair for SSH access to the instance.
  • ECR repository containing the Docker image for the EC2 instance.
  
Deployment Instructions:
------------------------
  • Open the AWS CloudFormation console or use AWS CLI.
  • Upload the template file: AIMaticEC2Stack.yaml.
  • Configure the parameters according to your requirements:

      Example:
        • InstanceType = t3.micro
        • KeyPairName = <YourExistingKeyPair>
        • DocumentInputBucketArn = <InputBucketArn>
        • DocumentOutputBucketName = <OutputBucketName>
        • ECRRepositoryUri = <Your ECR URI>
        • BedrockModelId = <ModelID>
        • Environment = sandbox-prod
        • OperatingSystem = AmazonLinux or Ubuntu
        
  • Optional parameters can be left empty if not needed.

  • Adjust VPC and Subnet settings if needed:
        • EC2Vpc.CidrBlock – Change VPC IP range.
        • PublicSubnet1 & PublicSubnet2 – Adjust subnet CIDR blocks or Availability Zones.
        • Add the IAM Policies permissions based on the requirement.
  
  • Configure Security Group ports based on your requirements:
        • SSH (default 22) – For SSH access
        • HTTP (default 80) – For web applications
        • Additional ports – Add as needed for your applications

  • OS Selection:
        • Choose between AmazonLinux or Ubuntu based on your preference.
  

Outputs from the Template:
--------------------------
  • After deployment, you can find the identifiers and addresses of the EC2 resources you created:

        • EC2 Instance ID – The instance created for AIMatic.
        • EC2 Public IP – Public IP of the instance.
        • EC2 Elastic IP – Associated Elastic IP.

Important Notes:
----------------
  • Ensure the Key Pair exists before deployment; it is required for SSH access.
  • IAM roles provide EC2 instance with access to S3, Textract, Bedrock, and ECR.
  • Docker is automatically installed on the instance based on the selected OS.
  • Adjust VPC, Subnet, Instance Type, OS, and Security Group ports based on your workload requirements.