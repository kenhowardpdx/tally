output "bastion_public_ip" {
  description = "Public IP of bastion host"
  value       = aws_instance.bastion.public_ip
}

output "bastion_id" {
  description = "Instance ID of bastion host"
  value       = aws_instance.bastion.id
}

output "bastion_ssh_username" {
  description = "SSH username for bastion host"
  value       = "ec2-user" # Change if using a different AMI
}

output "bastion_ssh_key_name" {
  description = "SSH key name for bastion host"
  value       = aws_instance.bastion.key_name
}

output "bastion_ssh_port" {
  description = "SSH port for bastion host"
  value       = 22
}
