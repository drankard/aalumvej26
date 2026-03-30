# DNS Setup — aalumvej26.dk

Domain registered at Hostinger. SSL via AWS ACM, served through CloudFront.

## ACM Certificate

- **ARN**: `arn:aws:acm:us-east-1:622327379339:certificate/d4006225-e2c7-49cb-80a2-b8073e8b10d0`
- **Region**: us-east-1 (required for CloudFront)
- **Domains**: aalumvej26.dk, www.aalumvej26.dk
- **Validation**: DNS

## Step 1 — Certificate Validation CNAMEs

Add these in Hostinger DNS to validate the ACM certificate:

| Type  | Name                                          | Value                                                               |
|-------|-----------------------------------------------|---------------------------------------------------------------------|
| CNAME | `_e39789bbd45a67f7c76a83d3bc455d55`           | `_f1cd39f4ffcc9e295455b14ebb265c20.jkddzztszm.acm-validations.aws.` |
| CNAME | `_29bfd22aee634f9310589119f2894b88.www`       | `_5cc2c092829f768965803032c1ea2c89.jkddzztszm.acm-validations.aws.` |

Keep these records — AWS re-validates periodically for cert renewal.

## Step 2 — Deploy CloudFront

Once the certificate status is `ISSUED`, add the ARN to the CI deploy.

In `.github/workflows/deploy.yml`, add to the `--parameter-overrides` line:

```
CertificateArn=arn:aws:acm:us-east-1:622327379339:certificate/d4006225-e2c7-49cb-80a2-b8073e8b10d0
```

Push to main. CI creates the CloudFront distribution (~5-10 min).

## Step 3 — Point Domain to CloudFront

After CloudFront is created, get the distribution domain from stack outputs:

```
aws cloudformation describe-stacks --stack-name aalumvej26 --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomain`].OutputValue' --output text
```

Then add in Hostinger DNS:

| Type  | Name  | Value                          |
|-------|-------|--------------------------------|
| CNAME | `www` | `d_________.cloudfront.net`    |
| A     | `@`   | See note below                 |

For the root domain (`@`): Hostinger doesn't support ALIAS records. Options:
- Use Hostinger's URL redirect: redirect `aalumvej26.dk` to `www.aalumvej26.dk`
- Or use a CNAME flattening service if Hostinger supports it

## Architecture

```
User -> aalumvej26.dk -> CloudFront (HTTPS, gzip, HTTP/2+3)
                            -> S3 Website (eu-west-1)
```

CloudFront provides:
- HTTPS with custom domain
- Gzip/Brotli compression
- Edge caching (global CDN)
- HTTP/2 and HTTP/3
- SPA routing (404/403 -> index.html)
