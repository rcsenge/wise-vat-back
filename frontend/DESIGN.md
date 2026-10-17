# SIGINT Frontend Design

## Purpose

The frontend connects a company with the VATBACK service. Employees scan company receipts in the web app. Employers review the scanned documents and see the total money the company can claim from the government.

## Stack

- HTML5 markup.
- Tailwind CSS v4 for styling.
- Caddy as the web server.

## Deliverables

- A web application for the employer.
- A web application for the employee.
- No government integration in this phase.

## Views

### 1. Transaction History (Employee App)

The employee app shows every scanned company receipt. Each entry shows the scanned document and its transaction details. The app renders the list from the backend API.

### 2. Document Scan (Employee App)

The employee presses the new document option. The page opens the camera. The camera captures the receipt image and stores the image in the history view.

### 3. Employer Review (Web)

The employer sees all scanned documents. The web app sums the claimable tax across the receipts. The employer sees the total money the company can claim from the government.

## Interaction Flow

1. The employee scans a receipt with the app.
2. The app stores the image and the transaction details.
3. The employer opens the web app.
4. The web app lists the receipts and the total claimable amount.

## Non-Goals

- Sending documents to the government.
- Backend or server-side logic.
- Authentication and user accounts.
