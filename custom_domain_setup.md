# Custom Domain Setup for Pittsburgh Steps Explorer

Follow these steps to configure a custom domain for your App Engine application:

## Prerequisites
- A registered domain name
- Access to your domain's DNS settings
- Google Cloud Platform project owner or editor role

## Steps

### 1. Verify domain ownership in Google Cloud Console

1. Go to [Search Console](https://search.console.google.com/)
2. Click "Add Property" and add your domain
3. Follow the verification steps (typically adding a DNS TXT record)

### 2. Map your domain to your App Engine application

```bash
# Replace yourdomain.com with your actual domain
gcloud app domain-mappings create yourdomain.com --project=annular-ray-445804-r8
```

### 3. Set up SSL certificates

```bash
# Create a managed SSL certificate for your domain
gcloud app domain-mappings update yourdomain.com \
    --certificate-id=auto \
    --project=annular-ray-445804-r8
```

### 4. Update DNS records

Add the following records to your domain's DNS configuration:

| Record Type | Name | Value |
|-------------|------|-------|
| A           | @    | See App Engine IP's provided after mapping |
| AAAA        | @    | See App Engine IP's provided after mapping |
| CNAME       | www  | ghs.googlehosted.com |

### 5. Verify mapping status

```bash
# Check mapping status
gcloud app domain-mappings list --project=annular-ray-445804-r8
```

It may take 24-48 hours for DNS changes to fully propagate and SSL certificates to be provisioned.
