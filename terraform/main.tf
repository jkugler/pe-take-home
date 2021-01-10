terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  profile = "default"
  region  = "us-west-2"
}

resource "aws_vpc" "web" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.web.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-west-2a"
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.web.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-west-2a"
}

resource "aws_internet_gateway" "web" {
  vpc_id = aws_vpc.web.id
  tags = {
    Name = "hedge-gateway"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.web.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.web.id
  }
}

resource "aws_route_table_association" "public_routing" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_eip" "nat" {
  vpc        = true
  depends_on = [aws_internet_gateway.web]
}

resource "aws_nat_gateway" "web" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id
  depends_on    = [aws_internet_gateway.web]
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.web.id

  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.web.id
  }
}

resource "aws_route_table_association" "private_routing" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "web" {
  name        = "web_server_sg"
  description = "Allow needed traffic"
  vpc_id      = aws_vpc.web.id

  egress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "elb" {
  name        = "elb_sg"
  description = "Allow needed traffic"
  vpc_id      = aws_vpc.web.id

  egress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "template_file" "init" {
  template = file("${path.module}/user-data.sh")

  vars = {
    docker_registry_host = var.docker_registry_host
    docker_image_name    = var.docker_image_name
  }
}

resource "aws_instance" "web" {
  ami                         = "ami-07dd19a7900a1f049"
  instance_type               = "t2.medium"
  subnet_id                   = aws_subnet.private.id
  user_data                   = data.template_file.init.rendered
  vpc_security_group_ids      = [aws_security_group.web.id]
  # These were being REALLY slow coming up for some reason
  # Didn't want package retreival to fail
  depends_on                  = [aws_nat_gateway.web]
  tags = {
    Name = "hedge-web"
  }
}

resource "time_sleep" "wait_for_user_data_script" {
  create_duration = "5m"
  depends_on = [aws_instance.web]
}

resource "aws_elb" "web" {
  name    = "hedge-elb"
  subnets = [aws_subnet.public.id]
  security_groups = [aws_security_group.elb.id]

  listener {
    instance_port     = 80
    instance_protocol = "http"
    lb_port           = 80
    lb_protocol       = "http"
  }

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    target              = "HTTP:80/env"
    interval            = 30
  }

  instances                   = [aws_instance.web.id]
  cross_zone_load_balancing   = false
  idle_timeout                = 400
  connection_draining         = true
  connection_draining_timeout = 400
  depends_on                  = [time_sleep.wait_for_user_data_script]
}
