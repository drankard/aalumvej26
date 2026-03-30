# DNS Setup — aalumvej26.dk

Domain registered at Hostinger. SSL via AWS ACM, served through CloudFront.

## ACM Certificate

- **ARN**: `arn:aws:acm:us-east-1:622327379339:certificate/d4006225-e2c7-49cb-80a2-b8073e8b10d0`
- **Region**: us-east-1 (required for CloudFront)
- **Domains**: aalumvej26.dk, www.aalumvej26.dk
- **Validation**: DNS
- **Status**: ISSUED

## CloudFront Distribution

- **Domain**: `dcpy1eir4hbjk.cloudfront.net`
- **Features**: HTTPS, gzip/brotli, HTTP/2+3, edge caching, SPA routing

## Hostinger DNS Records

### Certificate validation (keep forever — needed for auto-renewal)

| Type  | Name                                    | Value                                                               | TTL   |
|-------|-----------------------------------------|---------------------------------------------------------------------|-------|
| CNAME | `_e39789bbd45a67f7c76a83d3bc455d55`     | `_f1cd39f4ffcc9e295455b14ebb265c20.jkddzztszm.acm-validations.aws.` | 14400 |
| CNAME | `_29bfd22aee634f9310589119f2894b88.www` | `_5cc2c092829f768965803032c1ea2c89.jkddzztszm.acm-validations.aws.` | 14400 |

### Domain pointing

| Type  | Name  | Value                            | Notes                                              |
|-------|-------|----------------------------------|----------------------------------------------------|
| CNAME | `www` | `dcpy1eir4hbjk.cloudfront.net`   | Main entry point                                   |
| CNAME | `@`   | `dcpy1eir4hbjk.cloudfront.net`   | If Hostinger won't allow CNAME on root, see below  |

**Root domain fallback**: If Hostinger rejects a CNAME on `@`, delete the A record (`2.57.91.91`) and set up a URL redirect from `aalumvej26.dk` to `www.aalumvej26.dk` in Hostinger's redirect settings.

### Records to remove

| Type | Name | Old value     | Reason                          |
|------|------|---------------|---------------------------------|
| A    | `@`  | `2.57.91.91`  | Hostinger default, no longer needed |

## Architecture

```
User -> aalumvej26.dk -> CloudFront (HTTPS, gzip, HTTP/2+3)
                            -> S3 Website (eu-west-1)
```

## Rebuilding from scratch

If you ever need to redo this:

1. Request ACM cert in **us-east-1** for `aalumvej26.dk` + `www.aalumvej26.dk` with DNS validation
2. Add validation CNAMEs in Hostinger, wait for ISSUED status
3. Pass cert ARN as `CertificateArn` parameter in deploy workflow
4. Push to main — CI creates CloudFront (~5-10 min)
5. Update Hostinger DNS to point at the CloudFront domain from stack outputs
