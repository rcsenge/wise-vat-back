# SIGINT Frontend

Frontend for the VATBACK service. Read DESIGN.md for the product concept.
The app uses pnpm and the Wise Neptune CSS design system.

## Install

1. Install dependencies with pnpm: `pnpm install`
2. The install copies the Neptune assets to `www/vendor/neptune`.

## Serve the Employee Demo

1. Build the stylesheet once: `pnpm run build:css`
2. Serve the `www` folder with Caddy: `caddy run`
3. Start the backend on port 8000: `make dev-backend` in `../backend`.
4. Find this PC's LAN IP with `ipconfig`.
5. Open `http://<LAN-IP>:8080` in Safari on the iPhone.
6. Tap Add New Document. Select an invoice JSON file.

The `Caddyfile` serves clean URLs. It maps `/` to `index.html` and `/employer` to `employer.html`.

The file-input capture works over plain HTTP on iOS Safari. It does not need HTTPS.

## Backend Connection

`www/api.js` calls the backend on port 8000 of the page host.
`www/receipts.js` renders the receipt list on both pages.

- `POST /invoices/upload`: the employee page sends the invoice JSON. The backend returns the result with the reasons.
- `GET /receipts`: both pages list the stored receipts.
- `GET /claims`: the employer page shows the refundable VAT per country.

Sample invoices live in `../backend/backend/seed/invoices/`. Run `make seed` in `../backend` to reset the demo.
