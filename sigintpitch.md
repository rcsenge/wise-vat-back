# SIGINT · Wise VAT Back — 5 Minute Pitch

**Presenter script + timing cues.** Speak naturally. The section titles are cues, not slides. You have one screen: the countdown page on `/countdown`.

> **On screen during the whole pitch:** `/countdown` — a timer counts down from **05:00**.
> Under it, a number grows: the money the world loses while you talk.
> The figure runs at **€634 per second**, so about **€190,000** passes during your five minutes.
> Glance at it once or twice. Do not stare. Let the number land.

---

## 0:00–0:45 — The hook

Hi. I want you to meet a number that most companies never see.

Every year, you lose it. Not through bad luck. Through paperwork.

**SIGINT** is a small tool that finds that money and hands it to you in one click.

I will not show you APIs or code. I will show you a problem, and the five minutes of your life it steals.

---

## 0:45–1:45 — The problem

Here is the situation. Your team travels for business.

An employee lands in Berlin, or Vienna, or Warsaw. They stay in a hotel. They pay the bill. They pay the **VAT** — the sales tax on top of the price.

That tax does not belong to the hotel. It belongs to the government. But, when a company buys this as a business expense, **the company can get it back.**

This is not a trick. It is European law. It is called a **VAT refund**. Every EU country must allow it.

Here is the catch: **almost nobody claims it.**

Why? Because the paperwork is a nightmare. And the rules are different in every country.

---

## 1:45–2:30 — Why it is so hard

Let me make this concrete.

First, **the rules differ per country.** Austria refunds no VAT on fuel. France refunds none on hotel rooms. Poland refunds only half on fuel. Ten categories. Nine countries. Twenty different answers.

Second, **you must match every receipt to a real card payment.** One invoice, one transaction, right country, right date, right amount.

Third, **you only have until the 30th of September** the year after you travel. Miss it, and the money is gone. Forever.

So a finance person sits with a shoebox of paper and tries to work out, by hand, what is claimable. It is slow. It is boring. Most companies just **give up.**

The result: **€20,000,000,000 a year** in VAT that companies leave on the table.

Look at the screen. That is what passes during this talk.

---

## 2:30–3:30 — The solution

SIGINT makes the finance person's five-minute task **automatic.**

Here is the whole idea. You do your job. It does the rest.

1. The **employee** opens the app and uploads a receipt. A photo of a hotel bill, or a PDF.
2. A local AI **reads** it. It pulls out the supplier, the VAT number, the amounts, the date.
3. The backend **validates** it: is this a real invoice? Is the VAT number legitimate?
4. It **matches** the invoice to the right card transaction automatically.
5. It applies the **country rules** line by line, and says exactly what you can get back.

And here is the part I love: every single decision comes with a plain-English reason. It never says "no" silently. It tells you *why*.

No spreadsheets. No shoebox. No guessing.

---

## 3:30–4:15 — What you actually see

The employer opens one page.

You see **your refundable VAT, split by country.** Germany, Austria, Poland — each with its own total.

You see **deadlines** as a bar. Green when you have time. Red when it is urgent.

And when you are ready, you press **Generate all.**

That one button produces the **entire refund package** — the summary, the application lines, the invoice copies, and the audit trail — as a single ZIP file. Ready for your accountant to file.

The accountant saves hours. The company gets the money.

---

## 4:15–4:45 — Why this is a quality-of-life win

This is not a flashy dashboard. This is **quality of life.**

For the **employee**, claiming your expenses stops being a chore. You scan, you're done.

For the **finance team**, the fear of missing a deadline disappears. The app tells you.

For the **company**, money that was lost every year now comes back. Automatically.

The hardest part of VAT refunds is not the money. It is the **friction.** SIGINT removes the friction, not the rules.

The rules still apply. The law stays the same. We just make it something a human can actually do.

---

## 4:45–5:00 — Close

So, to recap.

**€20,000,000,000** is lost every year, mostly because it is too hard to claim.

SIGINT turns that mountain of paperwork into **one scan, one page, one button.**

The tax is real. The refund is real. The only thing in the way is friction.

And my favorite part — the model that reads the receipts runs **on your own machine.** No account. No API key. No internet. Your invoices never leave your computer.

Thank you.

---

## Notes for the presenter

- **Timer and money:** the growth number is the strongest prop. Let it run. A quiet beat where you and the audience watch it tick makes the point better than any slide.
- **Do not demo live unless asked.** If asked, use the sample invoice PDF in `backend/seed/documents/pass_de_hotel_berlin.pdf`.
- **Snappy exit.** At the 4:45 mark, stop the detail. Land the "your machine, your money" line and stop.
- **No Jargon.** Never say "Ollama," "VIES," "JSON," or "API" on stage. Say "a local AI" and "the package."
- **The numbers:** €20B/year lost, €634/second, ~€190k in five minutes. All from `frontend/www/countdown.js`.
