# AWS Cost Optimization Analysis

**Date**: December 21, 2025  
**Branch**: tally-6/costs

## Current Monthly Costs: $37.26

### Cost Breakdown by Service

| Service | Monthly Cost | Action |
|---------|--------------|--------|
| **RDS** | $16.95 | ❌ Eliminated |
| **EC2 Bastion** | $11.78 | ❌ Eliminated |
| **VPC** | $5.66 | ⚠️ Data transfer (minimize) |
| **EC2-Other** | $1.24 | ✅ Eliminated with bastion |
| **Route 53** | $1.00 | ⚠️ Required for domain |
| **Secrets Manager** | $0.62 | ✅ Eliminated (RDS removed) |
| **S3** | $0.00 | ✅ Free tier |
| **Lambda** | $0.00 | ✅ Free tier |
| **CloudFront** | $0.00 | ✅ Free tier |
| **Certificate Manager** | $0.00 | ✅ Always free |

## Optimizations Implemented

### 1. RDS PostgreSQL Eliminated (-$16.95/month)

**Removed**: 24/7 running db.t3.micro instance

**Alternatives for Development**:
- Local PostgreSQL via Docker Compose (already configured)
- Use `docker-compose up` for local development

**Alternatives for Production**:
- **Neon** (recommended): Serverless PostgreSQL with generous free tier
  - 0.5 GB storage free
  - Automatic scaling to zero
  - Compatible with PostgreSQL clients
  - **Cost: $0/month** (within free tier limits)
- **PlanetScale**: MySQL-compatible, generous free tier
  - **Cost: $0/month** (5 GB storage, 1B row reads/month)
- **Supabase**: PostgreSQL with free tier
  - **Cost: $0/month** (500 MB database, 2 GB bandwidth)
- **AWS Aurora Serverless v2**: PostgreSQL-compatible, scales with demand
  - **Minimum cost: ~$43/month** (0.5 ACU minimum × 730 hours × $0.12/ACU-hour)
  - Does NOT scale to zero (always minimum 0.5 ACU running)
  - Auto-scales between 0.5-128 ACUs based on load
  - Storage: $0.10/GB-month + I/O costs
  - **❌ NOT RECOMMENDED for cost optimization** - costs more than current RDS

### 2. Bastion Host Eliminated (-$11.78/month)

**Removed**: 24/7 running t3.micro instance

**Alternative for Database Access**:
- **AWS Systems Manager Session Manager** (free)
  - No SSH keys needed
  - Temporary instance access
  - Full audit logging
- **On-demand bastion**: Terraform module still exists, can be re-enabled when needed

### 3. Secrets Manager Eliminated (-$0.62/month)

**Removed**: Storage of RDS password

**Alternatives**:
- **AWS Systems Manager Parameter Store** (free for standard parameters)
- **Environment variables** in Lambda (for non-sensitive config)
- **External secret management** with free-tier database providers

### 4. EC2-Other Costs Eliminated (-$1.24/month)

**Removed with bastion**:
- EBS volume attached to bastion instance
- Elastic IP (if any)

### 5. VPC Costs Reduced (-~$3-4/month expected)

**Current**: $5.66/month (likely data transfer)

**Optimizations**:
- Already using zero-cost architecture (no NAT Gateway)
- Minimize data transfer between AZs
- Use CloudFront for static assets to reduce origin requests
- Lambda in single AZ where possible

**Remaining VPC costs** (~$1-2/month):
- Inter-AZ data transfer (unavoidable for multi-AZ)
- VPC flow logs if enabled (consider disabling in dev)

## New Estimated Monthly Costs: $1-2

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| Route 53 Hosted Zone | $0.50 | Required for domain management |
| Route 53 Queries | $0.20 | ~1M queries (first 1B free after hosted zone) |
| VPC Data Transfer | $0.50-1.00 | Inter-AZ and internet egress |
| S3 | $0.00 | Well within free tier |
| Lambda | $0.00 | Well within free tier (1M requests/month) |
| CloudFront | $0.00 | Within free tier (1TB data transfer) |
| **Total** | **$1.20-1.70** | **~95% cost reduction** |

## Annual Savings: ~$424

- **Before**: $37.26/month × 12 = $447/year
- **After**: $1.50/month × 12 = $18/year
- **Savings**: $429/year (96% reduction)

## Database Migration Plan

### For Development

Use Docker Compose (already configured):

```bash
cd /Users/ken/code/tally
docker-compose up -d postgres
```

Lambda will need updated environment variables to point to local database.

### For Production

**Recommended: Neon Serverless PostgreSQL**

1. Sign up at neon.tech (free tier)
2. Create database
3. Update Lambda environment variables:
   ```bash
   DB_HOST=<neon-host>.neon.tech
   DB_NAME=tallydb
   DB_USER=<neon-user>
   DB_PASSWORD=<neon-password>
   DB_PORT=5432
   ```
4. Use AWS Systems Manager Parameter Store (free) for secrets

**Configuration in Lambda**:
- Store connection string in Parameter Store
- Update Lambda IAM role to read from Parameter Store
- No Secrets Manager costs

## Next Steps

1. **Test locally**: Verify backend works with Docker Compose PostgreSQL
2. **Apply Terraform changes**: Run `terraform plan` and `terraform destroy` for RDS/bastion
3. **Set up production database**: Choose Neon or alternative
4. **Update Lambda environment**: Configure database connection
5. **Monitor costs**: AWS Cost Explorer to verify savings

## Potential Future Optimizations

### Further Cost Reduction to $0/month

**Option 1: Remove Route 53 (-$0.50/month)**
- Use CloudFront default domain (*.cloudfront.net)
- Trade-off: Lose custom domain

**Option 2: Use Cloudflare DNS (free)**
- Move DNS hosting to Cloudflare
- Keep domain registration elsewhere
- Savings: $0.50/month

**Option 3: Use Vercel/Netlify for Frontend (free tier)**
- Host Svelte app on Vercel (free tier)
- Remove CloudFront + S3 frontend
- Lambda API remains on AWS
- Savings: Minimal (already in free tier)

## Architecture Changes

### Before
```
Client → CloudFront → S3 (Frontend) + API Gateway → Lambda → RDS
                                                              ↑
                                                          Bastion (SSH)
```

### After
```
Client → CloudFront → S3 (Frontend) + API Gateway → Lambda → Neon/External DB
                                                              (Direct connection)
```

### Cost-Free Components
✅ VPC (subnets, route tables, internet gateway)  
✅ Security Groups  
✅ S3 (within free tier)  
✅ Lambda (within free tier)  
✅ CloudFront (within free tier)  
✅ Certificate Manager  
✅ API Gateway (within free tier)

### Minimal Cost Components
⚠️ Route 53 Hosted Zone ($0.50/month)  
⚠️ VPC Data Transfer ($0.50-1.00/month)

## Aurora Serverless v2 Cost Analysis

**❌ NOT RECOMMENDED for cost optimization**

### Why Aurora Serverless v2 Costs More

Aurora Serverless v2 sounds appealing but has critical cost implications:

1. **Minimum Capacity**: 0.5 ACU (Aurora Capacity Units) always running
   - Cannot scale to zero like Neon or other true serverless databases
   - 0.5 ACU × 730 hours/month × $0.12/ACU-hour = **$43.80/month**
   
2. **Additional Costs**:
   - Storage: $0.10/GB-month (vs $0.115 for RDS)
   - I/O: $0.20 per million requests
   - Backup storage: $0.021/GB-month
   - Data transfer: Standard AWS rates

3. **Total Minimum Cost**: ~$45-50/month for small database
   - **vs current RDS**: $16.95/month
   - **vs Neon**: $0/month (free tier)
   - **Verdict**: 2.5-3x MORE expensive than your current setup

### When Aurora Serverless v2 Makes Sense

Aurora Serverless v2 is valuable for:
- **Variable workloads** with unpredictable spikes (scales up automatically)
- **Enterprise applications** with strict SLAs requiring AWS-managed infrastructure
- **Multi-region** deployments with Global Database
- **Large databases** (>100GB) with high throughput requirements

### For Solo Developer / Side Projects

**Better alternatives**:

| Option | Monthly Cost | Scales to Zero | Notes |
|--------|--------------|----------------|-------|
| **Neon** | $0 | ✅ Yes | 0.5 GB free, perfect for side projects |
| **Supabase** | $0 | ✅ Yes | 500 MB free, includes auth & storage |
| **PlanetScale** | $0 | ✅ Yes | 5 GB free (MySQL-compatible) |
| **Docker Compose** | $0 | N/A | Local development only |
| **RDS t3.micro** | $16.95 | ❌ No | Current setup (being eliminated) |
| **Aurora Serverless v2** | $43.80+ | ❌ No | NOT cost-effective for small projects |

### Recommendation

Stick with the plan:
1. **Development**: Docker Compose (local PostgreSQL)
2. **Production**: Neon free tier (0.5 GB, scales to zero)
3. **Scale later**: If you exceed free tiers, upgrade to paid Neon (~$19/month for 10 GB) or consider Aurora only if you need >100 GB + high IOPS



```bash
# Review changes
cd /Users/ken/code/tally/infra
terraform plan

# Destroy RDS and bastion (careful!)
terraform destroy -target=module.rds
terraform destroy -target=module.bastion

# Or apply full changes
terraform apply

# Verify no running instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
aws rds describe-db-instances
```

## Rollback Plan

If you need to restore RDS/bastion:

```bash
# Uncomment modules in infra/main.tf
# Restore these sections:
# - module.rds
# - module.bastion
# - data.aws_secretsmanager_secret
# - data.aws_secretsmanager_secret_version

# Apply
terraform apply
```

## Notes

- **RDS Free Tier**: AWS offers 750 hours/month of db.t3.micro (single-AZ), but you were charged because it runs 24/7/30.5 = 732 hours, exceeding free tier in some months
- **EC2 Free Tier**: 750 hours/month of t2.micro/t3.micro, but bastion ran continuously
- **Secrets Manager**: No free tier ($0.40/secret + $0.05/10K API calls)
- **VPC**: Subnets, route tables, IGW are free; NAT Gateway would cost $45/month (already avoided)
