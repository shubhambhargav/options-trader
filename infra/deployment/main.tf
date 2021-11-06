resource "aws_iam_user" "deployment-algo-trader-user" {
    name = "bot-algo-trader-deploy"
    force_destroy = true

    tags = {
        "resource-name" = "algo-trader"
        "resource-env" = var.env
        "resource-name" = "deployment-maker"
    }
}

resource "aws_iam_user_policy" "deployment-access" {
    name = "deployment-access"
    user = aws_iam_user.deployment-algo-trader-user.name

    policy = file("deployment/policies/deployment-user.json")
}
