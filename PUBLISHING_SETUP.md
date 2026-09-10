# Medium + Pinterest publishing

The publishing adapter is downstream of production. It cannot consume an unapproved/unproduced product.

## Required GitHub Actions environment

Create a repository environment named `publishing` and add these **environment secrets**. Never commit them to the repository.

- `MEDIUM_INTEGRATION_TOKEN` — Medium integration token.
- `MEDIUM_USER_ID` — Medium user id associated with the integration token.
- `PINTEREST_ACCESS_TOKEN` — Pinterest API access token with permission to create Pins.
- `PINTEREST_BOARD_ID` — destination Pinterest board id.
- `PINTEREST_IMAGE_URL` — HTTPS image URL for the approved product Pin. The image must be publicly fetchable by Pinterest.

The workflow uses the `publishing` environment so repository secrets are not exposed to normal production jobs.

## Authentication / connection

Account authorization must happen outside this repository. The user creates the Medium/Pinterest API credentials in those services, then stores the values as GitHub environment secrets. The repository never stores the raw credentials.

## Safe defaults

- Medium is published as a **draft** by default (`MEDIUM_PUBLISH_STATUS=draft`). Change this deliberately only after validating the integration.
- The publishing workflow is manual (`workflow_dispatch`) and is separate from the production workflow.
- Production gates are not weakened or bypassed.
- A product must already have `used=Yes`, an approved review state, and an existing production package.
- Missing credentials or missing image URL fail closed.

## First connection test

1. Add the four secrets above to the `publishing` environment.
2. Run **Publishing - Medium + Pinterest** manually for a product already marked `Yes` (for example P020).
3. First test with Pinterest disabled and Medium enabled. Medium should create a draft.
4. Then test Pinterest with the approved image URL.
5. Only after both are independently verified should live publishing be enabled as a deliberate operational change.

## Important limitation

The current production package contains the generated copy and Amazon link but does not itself contain a hosted image URL. Pinterest therefore requires `PINTEREST_IMAGE_URL`. The image-generation/hosting step should be added as a separate adapter rather than inventing an image URL.

## Credential safety

Do not put tokens in `products.csv`, `review_state.json`, package files, commits, workflow inputs, logs, or issue comments. Do not echo secret environment variables. Rotate credentials immediately if they are ever exposed.
