output "bastion_public_ip" {
  description = "Public IP of bastion host"
  value       = aws_instance.bastion.public_ip
}

output "bastion_id" {
  description = "Instance ID of bastion host"
  value       = aws_instance.bastion.id
}
