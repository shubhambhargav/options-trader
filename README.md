# How-to

## Pre-requisites (Mac)
- [python 3.8](https://www.laptopmag.com/how-to/install-python-on-macos)
- python virtualenv
```
pip install virtualenv
```

Setup:
Go to the root folder of this repo, on the command line
```
cd options-trader
```

Create separate virtualenv and activate it
```
virtualenv -p python3.8 options-trader
source options-trader/bin/activate
```

Install requirements
```
pip install -r requirements.txt
```

To trigger the runner (only this command is required from next time onwards; after logging into Zerodha in Chrome)
```
python run.py
```

### Terraform / Infrastructure

- aws-vault installation (TODO: Add link)
- Local setup of aws-vault

```
aws-vault add <profile-name>
# Add access key and secret key
vim ~/.aws/config
# Add MFA details under the created config such as
# mfa_serial=arn:aws:iam::<account-id>:mfa/<username>
```

- The user used in the above step should have the following access:
    - AmazonEC2ContainerRegistryFullAccess
    - AmazonS3FullAccess
    - AWSCloudFormationFullAccess
    - AWSLambda_FullAccess
    - EC2FullAccess
    - IAMFullAccess
    - VPCFullAccess

1. Install [terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
```
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

2. Run terraform
```
cd infra
aws-vault exec <profile-name> -- terraform init
# Note: for the first time setup, backend needs to be commented out so that the first run can create it
aws-vault exec <profile-name> -- terraform apply
```

### Deployment

```
aws-vault exec <profile-name> -- sls deploy --stage prod
```
