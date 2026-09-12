# Medium + Pinterest publishing

Publishing is downstream of production. It cannot consume an unapproved/unproduced product.

## Current platform-safe design

### Medium

Medium is **manual-post only** in this project.

Medium's current Help Center says it no longer issues new integration tokens or allows new integrations, while existing tokens continue to work. Medium's API terms also prohibit using the API to post automatically generated content. Therefore this repository no longer attempts Medium API publishing.

The repository prepares a **Medium-ready Markdown package** from the already approved production content. Run **Prepare Medium Manual Post**, download its artifact, add the approved real images, human-edit/fact-check, and paste it into Medium manually.

### Pinterest

Pinterest remains the automated publishing target. Pinterest's API supports creating image Pins and requires an authorized access token with board/pin permissions; image Pins can use a public `image_url` media source.

## GitHub environment

Create exactly **one** repository environment named `publishing`.

Required Pinterest environment secrets:

- `PINTEREST_ACCESS_TOKEN` — Pinterest API access token with permission to create Pins.
- `PINTEREST_BOARD_ID` — destination board ID.
- `PINTEREST_IMAGE_URL` — public HTTPS URL of the approved real Pin image.

The old Medium secrets may remain in the environment, but they are no longer consumed by automated publishing.

## Pinterest validation

Run **Pinterest - Credential and Image Validation** manually.

It checks, without creating anything:

1. Pinterest token access.
2. Destination board access.
3. Public HTTPS image URL and image content type.

## Pinterest publishing

Run **Publishing - Pinterest** manually for a product that has already passed the production gates.

The workflow independently checks:

- `used=Yes`
- review `APPROVED`
- `approved_for_production=true`
- `draft_qc=PASSED`
- production package exists

The adapter also checks the target board for an existing Pin with the same Amazon link and blocks duplicate publication before POSTing a new Pin.

## Images

The automation does **not** invent replacement product images or rely on ephemeral GitHub Actions artifacts. `PINTEREST_IMAGE_URL` must point to the actual approved image hosted at a stable public HTTPS location.

For Medium, use the same approved real image as the first/featured image. Medium's guidance recommends putting the first image at the beginning of the story and setting it as the featured image.

## Credential safety

Never put tokens in `products.csv`, `review_state.json`, package files, commits, workflow inputs, logs, or issue comments. Never echo secret environment variables. Rotate a credential immediately if it is exposed.
