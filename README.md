# SIGINT Frontend

Frontend for the VATBACK service. Read DESIGN.md for the product concept.

## Serve the Employee Demo

1. Build the stylesheet once: `npm run build:css`
2. Serve the `www` folder with one option.
   - Option A (no install): `python -m http.server 8080 --directory www`
   - Option B (Caddy): `caddy file-server --root www --listen :8080`
3. Find this PC's LAN IP with `ipconfig`.
4. Open `http://<LAN-IP>:8080` in Safari on the iPhone.
5. Tap Add New Document to start the camera.

The file-input capture works over plain HTTP on iOS Safari. It does not need HTTPS.
