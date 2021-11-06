resource "aws_s3_bucket" "algo-trader-meta" {
    bucket = "algo-trader-meta"
    acl = "private"

    tags = {
        "Name" = "algo-trader-meta"
        "resource-env" = var.env
        "resource-group" = "algo-trader"
        "resource-name" = "algo-trader-meta"
    }
}
