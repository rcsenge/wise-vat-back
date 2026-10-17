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

## Recommendation

Adopt the hybrid ladder as the default.
Use Apple Vision OCR and rules for the fast path.
Keep qwen2.5vl:7b as the fallback for messy scans.
This is the only path to both speed and accuracy on this hardware.
