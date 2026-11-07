# Ng'ombe: a recorded herd

Cattle records for smallholders in Southern Province, Zambia: one record per animal, written by the people who know the
animal, over WhatsApp or a small web app, held on a machine in Zambia. Built by Zamai Solutions (Yumi Milling Ltd, Batoka)
with Anthropic's Claude Code. Demo and concept note: https://ngombe.zamai.pro

Status, November 2026: a working prototype in its first test with one translator and one herd. Nothing here is a product.
This repository holds the shape of the service: the app, the demo, the schema and the documents. The methods behind the
line, built over a year on a working business system, are not published.
The spec sheet (`app/spec-sheet.html`) says, item by item, what runs, what is to be built and what is research.

## What is in this repository

| Folder | What |
|---|---|
| `app/` | The static site served at ngombe.zamai.pro: the guided demo (`index.html`, installable), the live records app (`my/`), the spec sheet and the concept note, the ask page, the contact page. No build step. |
| `functions/` | Netlify functions: `ngombe-bind` ties a phone number to a profile through the WhatsApp line; `ngombe-api-url` publishes the backend's current address; `ngombe-ask` answers questions about the papers from a corpus. |
| `db/` | The Postgres schema for the self-hosted Supabase backend (`schema.sql`, then the numbered migrations), the terms shown in the app, and `SETUP.md`, how the backend is run. |
| `tools/` | Builders for the spec sheet and the concept note (Markdown to page to PDF) and the ask corpus. |

## How it runs

- **Backend**: Supabase (open-source Postgres, auth, storage) self-hosted in Docker on a small machine in Batoka, reached from
  the static app through a Cloudflare tunnel whose address the app fetches from `ngombe-api-url`. Row-level security:
  each person sees their own rows; entries are append-only and hash-chained in the database.
- **The line**: Meta's WhatsApp Cloud API on a number that also runs the ordinary WhatsApp app (coexistence). What a
  person sends is read and filed on the animal within seconds and answered in plain words. The operating code of the
  line is not in this repository; the spec sheet says what it does and what it costs.
- **Tonga**: our own translator, fine-tuned from NLLB-200 (not in this repository; NLLB-200 is under a non-commercial
  licence), reads Tonga; fixed Tonga lines in the app come from speakers, not from a model.

Secrets (database keys, the desk key, the Anthropic key, WhatsApp credentials) live in environment files and Netlify
environment variables, never here.

## Licence

PolyForm Noncommercial 1.0.0 (`LICENSE.md`): use, copy, change and share it for any non-commercial purpose. This work is
not for profit for as long as it is used to promote smallholder cattle farming in Southern Province: no subscriptions,
no charge to any farmer. Commercial use is discussed separately with Zamai Solutions (chris@zamai.pro).

How the small, local models behind this are made is described in the series Local AI for Zambia, paper 1: *A Chitonga-English Teacher Assistant for the Southern Province* (Zenodo, https://doi.org/10.5281/zenodo.23642662 ).

Built with Claude Code (Anthropic), Claude Fable 5.1, directed by Christoph Lindinger. Tonga by Matthew Sakala and the
speakers on the Zamai line.
