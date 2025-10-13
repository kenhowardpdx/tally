variable "ami_id" {
  description = "AMI ID for bastion host (use latest Amazon Linux 2)"
  type        = string
}

variable "subnet_id" {
  description = "Public subnet ID for bastion host"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID for bastion host"
  type        = string
}

variable "key_name" {
  description = "SSH key name for bastion host"
  type        = string
  default     = "tally-bastion-key-prod"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
}
