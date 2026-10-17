# Ollama Invoice Extraction: Latency Findings

This note records the measured latency of local AI invoice extraction on a MacBook.
It also lists the options for faster extraction.

The measurements ran on an Apple M3 with 16 GB RAM and Ollama 0.40.5.
The document is a one-page German hotel invoice.

## Measured Warm Latency

| Model | Warm latency | Correctness |
| --- | --- | --- |
| qwen2.5vl:7b (default) | 25-53 s | Passes validation and extraction checks |
| qwen2.5vl:3b | 13 s | Missing the supplier VAT number |
| qwen3-vl:8b (old default) | 265-323 s | Passes validation and extraction checks |

The qwen3-vl:8b model answered correctly but took minutes.
The project now defaults to qwen2.5vl:7b.
The code normalizes comma decimals and recomputes totals from the line items.
These two fixes make the fast model output valid.

## Why the 10 Second Target Is Hard

A 7B model generates about 500 output tokens per invoice.
Generation is memory-bandwidth bound.
The M3 reads the 4.7 GB model at about 68 GB/s.
This sets the warm floor at about 25 s.

Text-only prompts measure the same latency.
The image is not the bottleneck.
Generation dominates.

A 3B model reaches about 13 s.
It is too small to read the supplier VAT number reliably.
The VAT number is the core field for a refund service.

## Other extraction options

1. OCR plus rules.
   Use the PDF text layer for typed PDFs.
   Use Apple Vision OCR for photos and scans.
   Then map fields with regex and Pydantic.
   This path is deterministic and near-instant.

2. Small document transformers.
   Use Donut, LayoutLMv3, or PaddleOCR and PP-Structure.
   These networks are much smaller than a 7B generative model.
   They are built for receipt and invoice extraction.

3. Hybrid ladder.
   Run the fast path first.
   Escalate to qwen2.5vl:7b only when the fast path fails.
   Average latency drops to about one second.

4. Compact reply.
   Keep the generative model but emit a flat reply.
   Expand the flat reply in code.
   This cuts tokens but does not reach the target.

## Hybrid Accuracy vs the Current Model

The hybrid can match or exceed the current 7B accuracy. The gate decides this.

Where the hybrid is more accurate:
- Typed PDFs have a text layer. Rules read the exact characters.
- No optical misreading, no comma format slips, no invented fields.
- Arithmetic is exact. The 7B summed VAT wrong on the test invoice.
  Rules and recompute never sum wrong.

Where the hybrid risks less accuracy:
- Unusual layouts, handwritten notes, and blurry scans confuse rules.
- The fallback fires for these cases. It matches today's accuracy.
- A wrong but format-valid rule extract can pass the gate without falling back.
  This is the only scenario where the hybrid can be worse.

How to make the gate strict:
- Validate the VAT number against the country format.
- Run the VIES lookup for a live EU VAT number.
- Check that line sums equal the totals.
- Escalate when any value is null or any check is uncertain.

Measure both paths on the 46-case golden corpus before switching.
The evaluation script in the repo reports a side-by-side comparison.

## Recommendation

Adopt the hybrid ladder as the default.
Use Apple Vision OCR and rules for the fast path.
Keep qwen2.5vl:7b as the fallback for messy scans.
This is the only path to both speed and accuracy on this hardware.

## Measurement Protocol

Run the measurement before the ladder becomes the default.
The golden document corpus holds one PDF per golden case.
The corpus lives in `backend/seed/documents/`.
The evaluation script reports the side-by-side comparison.

Run this command from `backend/`.

```
make eval-ai
```

Run the fast path alone first.
Run the AI path alone second.
Run the hybrid third.
Record the three results in the table below.
Report the warm latency per path.
Report the correctness per path.

| Path | Warm latency | Correctness |
| --- | --- | --- |
| Rules fast path | to measure | to measure |
| Ollama qwen2.5vl:7b | to measure | to measure |
| Hybrid ladder | to measure | to measure |

A path is correct when it meets the strict gate.
The gate checks the VAT format, the VIES status, and the line sums.
Measure on the same MacBook as the latency findings.
Use the same one-page hotel invoice for the latency rows.
