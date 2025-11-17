variable "environment" {
    description = "Deployment environment (e.g., dev, prod)"
    type        = string
}

variable "project" {
    description = "Project name for tagging"
    type        = string
    default     = "tally"
}

variable "bucket_name" {
    description = "Name of the S3 bucket for backend assets"
    type        = string
}

variable "force_destroy" {
    description = "Allow S3 bucket to be destroyed even if not empty"
    type        = bool
    default     = false
}

variable "tags" {
    description = "Additional tags to apply to resources"
    type        = map(string)
    default     = {}
}
