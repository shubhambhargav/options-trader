output "vpc_id" {
    value = aws_vpc.algo-trader.id
}

output "subnet_ids" {
    value = aws_subnet.public-subnet.*.id
}
