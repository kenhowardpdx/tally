# Data source to get available AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project}-${var.environment}-vpc"
    Environment = var.environment
    Project     = var.project
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.project}-${var.environment}-igw"
    Environment = var.environment
    Project     = var.project
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.availability_zones)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project}-${var.environment}-public-${var.availability_zones[count.index]}"
    Environment = var.environment
    Project     = var.project
    Type        = "public"
  }
}

# Database Subnets (for RDS subnet group - still free!)
resource "aws_subnet" "database" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 2)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name        = "${var.project}-${var.environment}-database-${var.availability_zones[count.index]}"
    Environment = var.environment
    Project     = var.project
    Type        = "database"
  }
}

# NOTE: NAT Gateway and Elastic IP removed for zero-cost architecture
# Lambda functions will run in public subnets with security groups for protection

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.project}-${var.environment}-public-rt"
    Environment = var.environment
    Project     = var.project
    Type        = "public"
  }
}

# Public Route Table Association
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Database Route Table (shares public routing - still free!)
resource "aws_route_table_association" "database" {
  count = length(aws_subnet.database)

  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.public.id
}

# Lambda Security Group
resource "aws_security_group" "lambda" {
  name_prefix = "${var.project}-${var.environment}-lambda-"
  vpc_id      = aws_vpc.main.id

  description = "Security group for Lambda functions"

  # Outbound rules - allow all outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project}-${var.environment}-lambda-sg"
    Environment = var.environment
    Project     = var.project
    Purpose     = "lambda"
  }
}

# RDS Subnet Group (for use by RDS instance)
resource "aws_db_subnet_group" "rds" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id
  tags = {
    Name        = "${var.project}-${var.environment}-db-subnet-group"
    Environment = var.environment
    Project     = var.project
    Purpose     = "rds"
  }
  description = "Database subnet group for RDS"
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "${var.project}-${var.environment}-rds-"
  vpc_id      = aws_vpc.main.id

  description = "Security group for RDS database"

  # Inbound from Lambda (PostgreSQL)
  ingress {
    description     = "PostgreSQL from Lambda"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  tags = {
    Name        = "${var.project}-${var.environment}-rds-sg"
    Environment = var.environment
    Project     = var.project
    Purpose     = "rds"
  }
}

# Bastion Security Group
resource "aws_security_group" "bastion" {
  name_prefix = "${var.project}-${var.environment}-bastion-"
  vpc_id      = aws_vpc.main.id

  description = "Security group for Bastion host"

  # Example: allow SSH from your IP
  ingress {
    description = "SSH from anywhere (customize for security!)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project}-${var.environment}-bastion-sg"
    Environment = var.environment
    Project     = var.project
    Purpose     = "bastion"
  }
}
