# =============================================================================
# S3 Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name prefix for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "enable_versioning" {
  description = "Enable S3 bucket versioning (recommended for prod)"
  type        = bool
  default     = false  # Keep disabled for side project cost savings
}

variable "force_destroy" {
  description = "Allow bucket deletion even if not empty (use for dev only)"
  type        = bool
  default     = true
}

variable "lifecycle_days_to_archive" {
  description = "Days after which to move objects to Glacier (0 = disabled)"
  type        = number
  default     = 0  # Disabled by default for side projects
}

variable "lifecycle_days_to_expire" {
  description = "Days after which to delete objects (0 = never)"
  type        = number
  default     = 90  # Clean up old files after 90 days
}
