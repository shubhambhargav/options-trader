terraform {
    required_version = ">= 0.15"

    backend "s3" {
        bucket = "algo-trader-meta"
        key = "terraform.tfstate"
        region = "us-east-1"
    }
}

provider "aws" {
    region = var.aws_region
}

module "s3" {
    source = "./s3"

    env = var.env
}

module "vpc" {
    source = "./vpc"

    env = var.env
}

module "deployment" {
    source = "./deployment"

    env = var.env
    aws_region = var.aws_region
}

module roles {
    source = "./roles"

    env = var.env
}
