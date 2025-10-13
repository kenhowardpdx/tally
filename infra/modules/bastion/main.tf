# Bastion Host (Jumpbox) - Cost-Optimized

resource "aws_instance" "bastion" {
  ami                    = var.ami_id
  instance_type          = "t3.micro" # Free tier eligible
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  associate_public_ip_address = true
  key_name               = var.key_name
  tags                   = var.tags

  # Stop instance when not needed to save costs
}

output "bastion_public_ip" {
  value = aws_instance.bastion.public_ip
}
output "bastion_id" {
  value = aws_instance.bastion.id
}
