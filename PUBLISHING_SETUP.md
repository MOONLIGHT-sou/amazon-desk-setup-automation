# Medium + Pinterest publishing

The publishing adapter is downstream of production. It cannot consume an unapproved/unproduced product.

## Required GitHub Actions environment

Create exactly **one** repository environment named `publishing` and add these **environment secrets**. Never commit them to the repository.

- `MEDIUM_INTEGRATION_TOKEN` — existing Medium integration token.
- `MEDIUM_USER_ID` — Medium user id associated with the integration token.
- `PINTEREST_ACCESS_TOKEN` — Pinterest API access token with permission to create Pins.
- `PINTEREST_BOARD_ID` — destination Pinterest board id.
- `PINTEREST_IMAGE_URL` — HTTPS image URL for the approved product Pin. The image must be publicly fetchable by Pinterest.

The workflow uses the `publishing` environment so these secrets are not exposed to normal production jobs.

## Authentication / connection

Account authorization must happen outside this repository. The user creates or retrieves the service credentials in those services, then stores the values as GitHub environment secrets. The repository never stores raw credentials.

Pinterest currently requires an authorized API token with appropriate board/pin scopes for creating Pins. The repository's read-only validation workflow checks token access and board access before any Pin is created.

**Medium caveat:** Medium's current Help Center says it is not issuing new integration tokens or allowing new integrations, while existing integration tokens continue to work. Therefore this adapter is viable only if the supplied token is an existing working Medium integration token. The validation workflow performs a read-only `GET /v1/me` check and does not publish anything.

## Safe defaults

- Medium is published as a **draft** by default (`MEDIUM_PUBLISH_STATUS=draft`).
- The publishing workflow is manual (`workflow_dispatch`) and is separate from the production workflow.
- Production gates are not weakened or bypassed.
- A product must already have `used=Yes`, an approved review state, and an existing production package.
- Missing credentials or missing image URL fail closed.
- Credential validation is read-only and never creates a post or Pin.

## Connection validation

Run **Publishing - Credential Validation** manually from GitHub Actions after adding the secrets.

The validation checks:

1. Medium token authentication (`GET /v1/me`).
2. Pinterest token authentication (`GET /v5/pins`).
3. Pinterest destination board access (`GET /v5/boards/{board_id}`).
4. `PINTEREST_IMAGE_URL` is HTTPS and publicly fetchable as an image.

No publishing mutation occurs during this workflow.

## Publishing test

Only after credential validation passes:

1. Run **Publishing - Medium + Pinterest** manually for an already consumed/approved product.
2. First test with Pinterest disabled and Medium enabled; Medium should create a draft if the existing token remains valid.
3. Then test Pinterest with the verified image URL.
4. Verify the resulting Medium draft and Pinterest Pin manually.
5. Only after both are independently verified should automatic publishing be considered.

## Image source

The production package contains generated copy and an Amazon link but does not itself contain a stable hosted Pin image URL. `PINTEREST_IMAGE_URL` therefore must point to a real public image. Do not invent an image URL, use a private/local URL, or rely on an ephemeral GitHub Actions artifact URL.

A future image adapter should generate/use the approved product artwork and publish it to stable public hosting before the Pinterest step. The image adapter must remain separate from the production safety path.

## Credential safety

Do not put tokens in `products.csv`, `review_state.json`, package files, commits, workflow inputs, logs, or issue comments. Do not echo secret environment variables. Rotate credentials immediately if they are ever exposed.
