#!/usr/bin/env bash
# Build the Astro frontend against the live API and publish it to S3 +
# CloudFront. Single source of truth for "build, sync, invalidate" — called
# by:
#   - .github/workflows/deploy.yml            (code deploys, push to main)
#   - the aalumvej26-content-rebuild CodeBuild project (content-driven
#     rebuilds, triggered by the content pipeline Lambda)
#   - .github/workflows/rebuild-frontend.yml  (manual button)
#
# Requires: aws cli with credentials, node 20+, run from the repo root (or
# anywhere — paths resolve relative to this script).
set -euo pipefail

STACK_NAME="${STACK_NAME:-aalumvej26}"
REGION="${AWS_REGION:-eu-west-1}"

output() {
  aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

API_URL=$(output ApiUrl)
BUCKET=$(output FrontendBucket)
DIST_ID=$(output CloudFrontDistributionId || true)

if [ -z "$API_URL" ] || [ "$API_URL" = "None" ]; then
  echo "ERROR: ApiUrl stack output missing — refusing to build a contentless site" >&2
  exit 1
fi
if [ -z "$BUCKET" ] || [ "$BUCKET" = "None" ]; then
  echo "ERROR: FrontendBucket stack output missing" >&2
  exit 1
fi

cd "$(dirname "$0")/../frontend"

npm ci
VITE_API_URL="$API_URL" npm run build

aws s3 sync dist "s3://$BUCKET" --delete --region "$REGION"

if [ -n "$DIST_ID" ] && [ "$DIST_ID" != "None" ]; then
  aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
  echo "Frontend published: bucket=$BUCKET, invalidated distribution=$DIST_ID"
else
  echo "Frontend published: bucket=$BUCKET (no CloudFront distribution output — invalidation skipped)"
fi
