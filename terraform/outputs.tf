output "security-group-id" {
  value = aws_security_group.web.id
}

output "instance-id" {
  value = aws_instance.web.id
}

output "elb_dns_name" {
  value = aws_elb.web.dns_name
}
