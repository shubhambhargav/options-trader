resource "aws_vpc" "algo-trader" {
    cidr_block = "10.1.0.0/16"

    tags = {
        "Name" = "algo-trader"
        "resource-group" = "algo-trader"
        "resource-env" = var.env
        "resource-name" = "vpc"
    }
}

data "aws_availability_zones" "available" {}

resource "aws_subnet" "public-subnet" {
    count = 2

    availability_zone = data.aws_availability_zones.available.names[count.index]
    cidr_block = "10.1.${count.index}.0/24"
    map_public_ip_on_launch = true
    vpc_id = aws_vpc.algo-trader.id

    tags = {
        "resource-group" = "algo-trader"
        "resource-env" = var.env
        "resource-name" = "subnet"
    }
}

resource "aws_internet_gateway" "algo-trader-ig" {
    vpc_id = aws_vpc.algo-trader.id

    tags = {
        "resource-group" = "algo-trader"
        "resource-env" = var.env
        "resource-name" = "internet-gateway"
    }
}

resource "aws_route_table" "algo-trader-public-route-table" {
    vpc_id = aws_vpc.algo-trader.id

    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.algo-trader-ig.id
    }
}

resource "aws_route_table_association" "route-table-association" {
    count = 2

    subnet_id = aws_subnet.public-subnet.*.id[count.index]
    route_table_id = aws_route_table.algo-trader-public-route-table.id
}

resource "aws_security_group" "base-intra-vpc-access-sg" {
    name = "base-intra-vpc-access-sg"
    description = "Accepts data from incoming connections within VPC"
    vpc_id = aws_vpc.algo-trader.id

    ingress = [ {
        cidr_blocks = [ aws_vpc.algo-trader.cidr_block ]
        description = "All access"
        from_port = 0
        ipv6_cidr_blocks = [ "::/0" ]
        prefix_list_ids = []
        protocol = "tcp"
        security_groups = []
        self = false
        to_port = 0
    } ]

    egress = [ {
      cidr_blocks = [ "0.0.0.0/0" ]
      description = "All access"
      from_port = 0
      ipv6_cidr_blocks = [ "::/0" ]
      prefix_list_ids = []
      protocol = "-1"
      security_groups = []
      self = false
      to_port = 0
    } ]

    tags = {
        "resource-group" = "algo-trader"
        "resource-env" = var.env
        "resource-name" = "security-group"
    }
}