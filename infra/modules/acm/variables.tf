variable "domain_name" {
  description = "The domain name for the ACM certificate."
  type        = string
}

variable "subject_alternative_names" {
  description = "Subject alternative names for the ACM certificate."
  type        = list(string)
  default     = []
}

variable "validation_method" {
  description = "Validation method for ACM certificate (DNS or EMAIL)."
  type        = string
  default     = "DNS"
}

variable "tags" {
  description = "Tags to apply to ACM resources."
  type        = map(string)
  default     = {}
}
