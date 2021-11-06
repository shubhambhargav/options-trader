resource "aws_iam_role" "options-trader-lambda-role" {
    name = "${var.env}-options-trader-lambda-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Sid = ""
                Principal = {
                    Service = "lambda.amazonaws.com"
                }
            },
        ]
    })

    inline_policy {
        name = "LambdaAcess"
        policy = jsonencode({
            Version = "2012-10-17"
            Statement = [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "ec2:CreateNetworkInterface",
                        "ec2:DescribeNetworkInterfaces",
                        "ec2:DeleteNetworkInterface",
                        "ec2:AssignPrivateIpAddresses",
                        "ec2:UnassignPrivateIpAddresses"
                    ],
                    "Resource": "*"
                }
            ]
        })
    }
}