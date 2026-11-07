# The recorded herd: what would be needed

Spec sheet v0.3, 7 November 2026. Zamai Solutions. Companion to the demo at ngombe.zamai.pro and to
`CATTLE_APP_SPEC.md` (the product spec) and `CATTLE_PROGRAMME_CONCEPT.md` (the programme). Every item is
marked by how far it is from working: **Have** (exists and runs today), **Configure** (exists, needs setting
up), **Build** (software to write, known how), **Collect** (data that must be gathered in the field),
**Research** (not known to work here until tested). Costs are not given; where a number appears it is marked
rough. Nothing in this sheet is a commitment.

---

## 1. Ready today

| Item | Status | What it is, and what it gives the cattle work |
|---|---|---|
| Postgres database with row-level security | Have | Supabase, the open-source Postgres stack, with the same row rules we already run a business and the Tonga tool on. For the cattle work it is self-hosted: on our own machine first, in a Zambian data centre when a ministry owns it; the hosted version only for the demo. One database, many small apps; each role sees its own rows. Append-only event tables, hash-stamped, as the demo describes. |
| WhatsApp as one front door | Have | A working line (+260 776 621 255) with inbound and outbound messaging, templates, documents and images, and a responder that reads messages and creates entries in the database from them. In the records system we run this turned out to be the most used way in: people send what they already send, a photo and a few words, and the system makes the entry and asks one question if something is missing. The barrier is as low as it gets: the sender's number is registered to one person, so the message arrives with that person's rights, no login, no password, no install. For the cattle work we offer it as an option, a proven method that makes usage natural; which door fits which place is an open question (section 6). |
| Offline-first web app | Have | The Chitonga tool is an installable web app that works without signal and syncs later; the cattle demo is built the same way. Android first, cheap phones. |
| Tonga translation | Have, improving | Our own Tonga translator (zamai.pro/tonga) and a desk of Tonga speakers who check it. For the app the rule is stricter: every label and every health line comes from a speaker, not the model. Matthew Sakala is translating the demo's 300 lines now. |
| Speaker network | Have | Translators and reviewers on the Zamai line (a teacher, a priest, field officers), paid per line when paid, with a working payment and balance routine. |
| Local compute | Have, small | A local machine for models that must stay in the country (the Tonga model runs there); rented GPU time for training runs. Enough for a few thousand pictures, not for a province. |
| Photo quality control over WhatsApp | Have, in another domain | A working routine that receives photos on WhatsApp, checks them and replies, built for Yumi Milling, the maize mill in Batoka that funds this work. The same mechanics serve the standard cattle picture. |
| Records expertise | Have | We build and run records systems with row rules, stamps and many apps on one database. This is not new ground. |

## 2. To configure

| Item | Status | Notes |
|---|---|---|
| SMS for feature phones | Configure | Many herders have no smartphone. An SMS gateway (local aggregator or the mobile operators) for reminders and one-line reports; USSD if a menu is needed. Cost per message is the open point, not the technology. |
| Separate database project for the cattle work | Configure | Its own project, so no other business's data sits beside it. Same stack. |
| Netlify or equivalent hosting of the apps | Have | Already hosts everything we publish. |
| Map tiles for the early-warning and movement screens | Configure | Open map tiles cached for the districts in question, so the maps work offline. |

## 3. To build (software, known how)

| Item | Status | What it is |
|---|---|---|
| The record store | Build | Animal, owner, herd, event, movement, photo, carcass tables; append-only; hash chain per animal; row rules per role. Weeks, not months. |
| The intake form (feedlot gate) | Build | Standard pictures, weight from the scale, condition, age, origin, health tags. Shown working in the demo. |
| A dedicated chat app, if WhatsApp is not wanted | Build | The same conversational way in, as our own app: a photo and a few words make an entry, Tonga throughout, works offline and syncs later, and nothing passes through a foreign company's servers. The right choice where data security or sovereignty rules out WhatsApp, for instance for a ministry. More to build and to get installed than WhatsApp; the same entries behind it. |
| The herder and owner apps | Build | Register, sick report with urgency rule, dip and vaccination, herder-to-owner, the record, selling. Icons first, little text, Tonga labels. |
| The vet case flow | Build | A case with photos and history to a vet, a reply, "visit needed". The app sorts by urgency; it never diagnoses. |
| The movement entry | Build | One tap at the dip tank, the sale pen, the gate, the abattoir; GPS of the place; this is the export record. |
| The early-warning view | Build | Sick reports by place and date; clusters around a dip tank; a list for the camp officer. Rules first, no model needed. |
| The abattoir entry | Build | Carcass weight, grade, condemnations, linked to the animal's ID. Depends on the abattoir's willingness and its own records. |
| The export check | Build | A rule over the movement record and the restricted-zone register: eligible, or not and why. Depends on the veterinary department publishing zones as data. |
| Data quality procedures and training | Build, then Collect | The condition for every model: one written procedure per entry (standard picture, weight, identity, health, events, carcass), a guide on the screen, a quality check on the phone that refuses a bad entry, training and testing of meat inspectors, dip-tank recorders, camp officers and herders, pay per verified entry, a second recorder on a sample, and a monthly loop from the model's errors back to training. None of this exists for Zambian cattle yet; it is written, tried at one dip tank and one abattoir, and changed by what breaks, before any model is trained. |
| Price pooling | Build | Median by class and weight band from members' sales and auction lists. |
| Ministry view | Build | Counts, coverage, movements, clusters; never a farmer's money. |

## 4. To collect (data the field must produce)

| Item | Status | What is needed |
|---|---|---|
| Picture pairs for weight and condition | Collect | A standard picture (side, full length; from above in the crush) paired with a scale reading, the same day. Rough need: several thousand pairs across breeds, ages and seasons before a model is worth checking; tens of thousands for one worth trusting. A feedlot produces hundreds a cycle. |
| Picture series per animal | Collect | The same animal every day for a cycle, from fixed cameras, with weights every two weeks. This gives growth, not just weight. |
| Carcass pairs | Collect | The live picture at exit paired with cold carcass weight, grade and condemnations from the abattoir. Needs the abattoir's data, not just a camera. |
| Health events with pictures | Collect | Sick reports with signs, pictures and the vet's outcome. Thousands before any model; useful as a record from the first one. |
| Muzzle pictures | Collect, Research | Two pictures a week apart of the same known animals, hundreds of animals, to test matching here (see 6). |
| Movement history | Collect | From the first day the entries exist. No model needed. |
| Prices | Collect | Auction lists are public; members' sales need consent. |
| Standard picture protocol | Build then Collect | Distance, angle, marker for scale, light; a one-page sheet and a phone overlay. Without it the pairs are noise. |

## 5. To train (models) and what they need

| Model | Status | Needs | Honest view |
|---|---|---|---|
| Weight and condition from a standard picture | Research | The pairs in 4; a held-out set never shown to the model; a field check against the scale. | Published work exists on this; none of it was done in a Zambian crush pen with Zambian breeds. Expect it to work for condition first, weight second. |
| Carcass estimate from the live animal | Research | The carcass pairs; one abattoir's grading convention. | Second cycle at the earliest. |
| Animal identity from the muzzle | Research | See 6. | Plausible; unproven here. The tag stays the identity. |
| Animal detection and counting in camera views | Build with existing models | Off-the-shelf detectors, fine-tuned on our camera views. | The easiest model. Counting at a dip tank is useful on its own. |
| Early-warning clustering | Build, no training | Rules on place, date and signs. | A model only after a season of reports. |
| Tonga interface | Have | Speakers, not the model, for every label. | Done the way the Tonga tool is done. |

Training runs on rented GPU time; inference for detection can run on a phone or a small local machine. Local
hosting for anything the ministry would own.

## 5b. Hardware: three options by available funds, and what we suggest

Prices are rough estimates in US dollars at November 2026 list prices from memory, before import duty, transport
and VAT, and must be checked before any purchase. Kwacha at about K19.5 to the dollar. The hardware is readily
available and is not the hard part. The hard part is people trained and data collected; the models can be
trained on rented machines for as long as needed.

| Option | What it is | Hardware, rough, US dollars | Risks and notes |
|---|---|---|---|
| A. Minimal pilot | Four or five Android phones that can do the job: a good main camera (12 megapixels or more, decent in the low light of a lairage), a large battery (5,000 mAh class), 128 GB of storage, a recent Android, and either a rugged model or a sturdy case; a mid-range Samsung A-series class phone does it, a rugged XCover class phone better. The person at the feedlot crush, the abattoir staff and the meat inspectors take the standard picture at the gate, the lairage and the hook, each trained in an afternoon. Database and apps on our existing machine. Models trained on rented GPU hours (about US$2 an hour; US$50 to 100 per model). | **US$1,000 to US$2,000**, about K20,000 to K40,000 | Nothing to install, nothing to steal. Depends entirely on the people keeping to the picture protocol. |
| B. Pilot with cameras | A plus two camera boxes where there is a mount and power: mains at the abattoir lairage, a small solar set at one dip tank or spray race. A dedicated central box with backups and a UPS. Training still rented, or one GPU workstation if runs become weekly. | **US$6,000 to US$11,000**, about K120,000 to K215,000 | Theft and weather at the dip tank; a camera needs a committee that wants it. The first pictures nobody has to take by hand. |
| C. Full-scale pilot | Twenty camera boxes at strategic places across a district or two: dip tanks, spray races, sale pens, the abattoir, each with a small solar set where there is no mains. Thirty phones of the same class. A local training machine with one or two GPUs, placed inside the provincial headquarters, with a second machine, a NAS and an off-site copy for redundancy, and a UPS. | **US$35,000 to US$50,000**, about K700,000 to K1,000,000, plus installation, data bundles and a service contract, OPEN | Theft of solar panels and boxes is the known risk; a box is only worth placing where someone is responsible for it. The models and the data stay in the province. |

**What we suggest.** Start with A, because it tests the only things that matter first: whether people keep to the
picture protocol, whether the pairs come in, and whether a first model checks out against the scale. Move to B
when the pairs are worth more than the people can take by hand, and to C when a district or a ministry wants the
data to stay with it and will own the machine. Hardware can be bought in a week at any point; a trained meat
inspector and a cycle of pairs cannot. Rented GPUs carry the training for as long as needed; a machine of our
own, or the province's, is a decision about ownership and sovereignty, not about speed.

**Ownership.** Before the first model is trained, three things must be settled in writing. The records are held
and owned by the system's operator under terms of service that the cattle owner accepts at registration; the
owner has access to their own animals' records, the right to correct them, and a say over who sees them beyond
the system's stated uses. Ownership by each cattle owner would make every later use a negotiation and is not
proposed. The aggregate (counts, coverage, movements, clusters) goes to the ministry, and tracking sick animals,
movements and outbreaks is never conditional on an owner's consent: that is animal health, but a record that names an owner, her number and her kraal is personal data under the Data Protection Act 2021, and is handled as such. The models belong to
whoever is set up to hold them. One structure worth considering is a special purpose vehicle in which
the people who supply the data (farmers through their cooperatives, the feedlot, the abattoir), the partners who
build, and government hold the models and the aggregate together, so that none of them can take the whole, and
a change of project or of supplier does not take the models with it. Open: the form, the shares, who chairs it.

The items below are the parts the three options are made of.

| Item | Phase 1 with cameras: one feedlot, one abattoir, one dip tank | Province scale |
|---|---|---|
| Phones at the gate, the crush, the dip tank | Android phones with a good main camera (12 megapixels or more, usable in a dim lairage), a 5,000 mAh class battery, 128 GB, a recent Android, and a rugged model or a sturdy case; a spare charger and a power bank per place. The standard picture is a phone picture; no special camera. **Rough: US$200 to 350 each; four or five, US$1,000 to US$1,750.** | One per recording place; a hundred places, US$25,000 to US$35,000. |
| Camera boxes (after the minimal pilot) | Two sites, where there is a mount and power: mains at the abattoir, solar at the dip tank. Each: a Raspberry Pi 5 class computer with a camera module (about US$150) or a Jetson Orin Nano kit (about US$300), solar panel, battery and controller (US$250 to 400), 4G router (US$80), weatherproof housing and pole (US$100). It takes a still a few times an hour or on motion, compresses it and sends it when there is signal; it runs no model. **Rough: US$600 to 900 per site, US$1,200 to US$1,800.** | A hundred sites at US$700: US$70,000. Installation and a year of 4G data on top, OPEN. |
| Video | None, except a ten-second clip per animal at the weigh crush, triggered by the gate. No extra hardware. | Same. Continuous video would need about one GPU per ten to thirty streams, plus bandwidth and power; not in the design. |
| Central machine: database and apps | Self-hosted Supabase on one Linux box: 16 to 32 GB RAM, 2 TB SSD, a second disk and off-site copy for backups, UPS. Our existing machine carries phase 1. **Rough: 0 now; US$1,200 to US$1,800 for a dedicated box; UPS US$200.** | A server in a Zambian data centre, two for redundancy. Rental per month OPEN; a cloud equivalent is US$100 to 300 a month. |
| Central machine: model training | Rented GPU hours first (about US$2 an hour; US$50 to 100 per model). A workstation with one consumer GPU of 24 to 32 GB (RTX 4090 or 5090 class), 64 GB RAM, 4 TB SSD only when runs become weekly. **Rough: under US$100 per model rented; US$3,500 to US$6,000 for the workstation.** | One or two GPUs; training stays nightly. US$6,000 to US$12,000. |
| Alternative: NVIDIA DGX Spark | One box with 128 GB unified memory. Does the same vision training, somewhat slower per dollar than a 5090 workstation, and also carries the Tonga language model locally. **Rough: US$4,000.** | Two boxes, 8,000, if language and vision share the machines. |
| Inference | Runs on the training GPU in minutes a day, or on a CPU within the day. No extra hardware. | Same, scaled. |
| Storage | A still is 100 to 300 KB; one site at fifty stills a day is a few GB a year. Covered by the SSDs above. | A hundred sites: about a gigabyte a day, under half a terabyte a year. A NAS for backups, US$600 to 900. |
| Power at sites | Solar panel, battery and charge controller per camera box, included above. Dip tanks and crush pens have no mains. | Same, per site. |
| Connectivity | 4G where it exists, store-and-forward where it does not; the phones sync when they reach signal. A 4G data bundle per site per month, OPEN. Where there is no signal at all, which is the case at many rural dip tanks, a satellite terminal at the dip tank: Starlink has served Zambia since 2023; the small terminal draws 25 to 40 W, the standard one 50 to 75 W, so the site's solar set grows by a panel and a battery. The dish is then also the dip tank's connection on dip day, for the herders' phones and the camp officer. **Rough: US$250 to 600 per kit, US$30 to 60 a month; Zambian prices OPEN.** | A satellite terminal at every site without signal; the share of sites is OPEN. |
| Securing the site | The camera box, the dish and the solar set are a community asset, which is a risk and a protection at once. Options: the dip tank committee holds custody and names a keeper; the kit is mounted high on the dip tank's own structure or a pole, in a locked steel box; the camera watches its own site; the terminal is registered to the project, so a stolen dish is switched off remotely and worthless; a small insurance line per site. Open: what the committees ask for. | Same, per site; the committee rule is what scales. |
| Messaging | WhatsApp messages are priced by Meta per delivered message, by market and category (the Zambia rate card is OPEN); SMS by the operators per message. Both OPEN for Zambia; small against the rest. | Scales with users; the one running cost that grows with success. |

The people, the feedlot cycle and the Tonga speakers are not in any of these numbers.

**Province scale, beyond the pilot options, hardware only, rough:** a hundred camera sites 70,000, phones US$25,000 to 35,000,
servers and GPUs US$20,000 to US$30,000: **of the order of US$120,000 to US$140,000 dollars**, plus installation, data
bundles and a data centre contract, all OPEN. These are the numbers a tender would start from, not end at.

## 6. Unresolved questions, with the options

1. **Identity: muzzle, tag, or both.** The Animal Identification Act requires official tags, and the mandated
   system has reached a tenth of its target. Muzzle matching reads the nose ridge pattern, independent of the
   coat, so uniform breeds are not the problem; wet or muddy noses, light, movement and growing calves are.
   Options: tag as the identity and muzzle as a check against tag loss and fraud; or, where tags have not reached, the muzzle as a
   provisional local record, never a substitute for the official identity. Test: thirty to a hundred known animals, photographed twice a week apart, matched on our
   phones. Kill test for the muzzle route.
2. **Where the record is written.** Dip tank, sale pen, feedlot gate, abattoir, vet camp, checkpoint, milk
   centre. Never one place only. Open: which places have a person and a phone every time an animal passes.
3. **GPS on some animals in large herds.** A collar or ear-tag with GPS on a few animals per herd would give
   movement without a person writing it. Open: cost per unit, battery, theft, and whether a few animals stand
   for the herd. Option: start without, with the place of every entry (the dip tank's GPS) as the movement
   record, and add collars in big herds and near borders later.
4. **The herder's phone as the sensor.** The phone's GPS at each entry gives place for free; a background
   track would give the herd's range. Open: consent, battery, coverage, and whether the herder's phone is his
   own. Option: GPS only at the moment of an entry, never a track, until someone asks for one.
5. **WhatsApp, a dedicated chat app, or screens.** WhatsApp is proven and natural but runs over a foreign
   company's servers. If that is not wanted, for data security or sovereignty, the same chat is built as a
   dedicated app on servers in Zambia, at the cost of getting it installed. Screens with icons suit the
   intake and the record views. Likely all three, by place and by role. One more fact for the choice: the
   Tonga translator sits on NLLB, Meta's open model, and the line runs on Meta's WhatsApp platform, so the
   project already builds on two things Meta gives away; government itself works on Facebook daily. Whether
   Meta would support the project in some form is an open question worth asking, with the dedicated-app
   route kept as the exit.
6. **Feature phones.** SMS and USSD cover them for reminders and one-line reports, not for pictures. Open: the
   share of herders with a smartphone in the pilot area. Where there is a smartphone, WhatsApp is one way
   in that needs no install.
7. **Cameras in the field.** Power (solar), connectivity (4G, store-and-forward, or a satellite terminal where there
   is no signal), weather, theft, and the dip tank committee's welcome. A community asset can be secured as
   communities secure the dip tank itself: custody, a keeper, a locked mount, a remotely disabled terminal. Option: a
   phone on a pole before any camera.
8. **Whose data.** The system's, under terms of service accepted at registration (in Tonga, read aloud where
   needed); the owner sees and corrects their own animals' records and has a say over sharing beyond the stated
   uses; the ministry sees counts and movements. The Data Protection Act applies to the personal data in the
   records, names and numbers, whatever the terms say. It does not stop a sick animal, a movement or an
   outbreak being tracked: the animal record carries personal data wherever it identifies a person, and the Act applies to it, and reporting notifiable disease is a duty
   under the Animal Health Act in any case. The two laws sit side by side; the terms of service say which
   person sees which record, not whether the disease is followed. Open: the terms themselves, and how a herder accepts
   them for an owner who lives elsewhere.
9. **The mandated system.** Who runs it, what it records, whether it exposes an interface. Option: write our
   record under it, never beside it. Ask the veterinary department early; this decides the export value.
10. **Who pays after a pilot.** Government, buyers, lenders, insurers, cooperatives, farmers. None proven.
   Option: the cooperative as the first payer for the price and dip modules, the abattoir for the carcass link.
11. **Vets and vaccines.** If the shortage is vets, vaccines or dip chemicals, information alone moves little.
    Test early with one camp officer and one vet.
12. **Use without chasing.** Smallholder apps die with their projects. The only verdict is herders who keep
    using it. WhatsApp as a way in is one answer: no install, no new habit. Test: ten herders shown the mockup
    and the WhatsApp way side by side.
13. **The abattoir's willingness.** Carcass data is theirs; the link needs their yes and their grading
    convention. One abattoir in Choma is enough to start.
14. **Who owns the models.** The records are the operator's under the terms of service, the aggregate the
    ministry's; the models need a holder. Option: a special purpose vehicle of the data suppliers, the builders and government (5b).

## 7. What is not needed first

Muzzle identification, drone or fixed-camera views, weight from a photo, breeding models, credit. All of them
depend on the pairs that the first cycle produces. The first build is the record store, the intake form, the
sick report and reply, and the movement entry.

## 8. Sequence, as a list

1. Partners: one feedlot, one abattoir, one vet, one dip tank committee. Ask the veterinary department.
2. Protocol: the standard picture sheet; the intake form; consent in Tonga.
3. Build: record store, intake, sick report, movement entry. Tonga labels from speakers.
4. Train the people: the person at the crush, the abattoir staff and the meat inspectors, on the standard
   picture and the entry, an afternoon each.
5. Collect: one feedlot cycle of pairs; the muzzle test; a season of sick reports and dips.
6. Check: the first weight model against the scale, on animals it has never seen.
7. Decide, with the numbers, what phase two is.

## 9. How this is built, in the open

Everything on this sheet was made by one person and one tool, and every piece below names what it runs on, who else sees the data, and what licence it sits under. What it does not describe is how the line reads and decides: the methods behind that were built over a year on a working business system and stay with us; the partners get them through the service, not as a handover.

| Piece | What it is | Where it runs, who sees the data | Licence, limits |
|---|---|---|---|
| The development | Written with Anthropic's Claude Code, working with the Claude Fable 5.1 model: the demo, the records app, the WhatsApp line, this sheet and the concept note. One developer, Christoph Lindinger, directs it; the tool writes and tests; what it writes is read before it ships. | Code on our machines. The app, the demo, the database schema and these documents are public at github.com/zamai-zambia/ngombe; the line's operating code is not. How small, local models are made for Zambia is written up in the series Local AI for Zambia, paper 1, *A Chitonga-English Teacher Assistant for the Southern Province*, https://doi.org/10.5281/zenodo.23642662 | PolyForm Noncommercial 1.0.0: any council, ministry or non-commercial body may take the code and run it themselves; commercial use is discussed with us. Not for profit for as long as the work serves smallholders in Southern Province. |
| The records | Supabase, the open-source Postgres stack, self-hosted in containers on a small machine in Batoka: Christoph's own, on solar backup, connected by Starlink Mini. Row-level access, append-only entries, hash-stamped. Photos sit in the same machine's storage. The app on the phone is static files served from ngombe.zamai.pro and talks to that machine through an encrypted tunnel. | The records stay in Zambia, on that machine. One machine, no redundancy yet; a second, stronger machine arrives in the week of 10 November; a Zambian data centre when a ministry owns the system. | Supabase and Postgres: open source. |
| The WhatsApp line | Meta's WhatsApp Cloud API on +260 776 621 255, on a number that also runs the ordinary WhatsApp app. A message is read within seconds and what it says is filed on the animal; the reply is written for the person, not from a script. Today the reading uses a hosted model (Claude Sonnet 5.5 through Anthropic's API; measured on 7 November 2026 at about US$0.004 and seven seconds a message). | Message text and photos pass through Meta (WhatsApp) and, for the reading, through Anthropic's API abroad. Every exchange is kept on our machine. | The goal is a local model on our own machine doing this reading, which needs a few thousand real exchanges first and is tested beside the hosted model before any switch. The rules of the service (no diagnosis, what goes to a person, how a number is tied) are ours and are not in any model. |
| Tonga, written | Our own translator, fine-tuned from Meta's NLLB-200 and checked by a desk of Tonga speakers; the line reads Tonga through it. Every fixed Tonga line a herder sees comes from a speaker, not from the model. | The translator runs on a hosted machine abroad (a Hugging Face Space) for now; the text sent for reading passes through it. | NLLB-200 is released under a non-commercial licence (CC BY-NC 4.0). That fits this not-for-profit use. A commercial application would need a translator trained on a permissively licensed base; the data and the method carry over. |
| Tonga, spoken | Planned, not built: speech to text for voice notes and a Tonga voice for replies. | Would run on our machine. | Needs tens of hours of transcribed Tonga speech and a few hours of one recorded speaker: paid work for speakers, beyond what we fund internally. |
| The visual models | Planned, not built. Candidates: a pretrained image backbone (DINOv2, ConvNeXt) with a small head trained on our scored pictures, a nearest-neighbour baseline on SigLIP embeddings, or a small vision-language model fine-tuned (PaliGemma, Qwen-VL). Targets, in order: body condition score; an age estimate from frame and teeth; weight; carcass quality from the live animal, against the abattoir's grading. A separate model from the one reading messages, always. | Would run on our machine or a phone. Pictures are already stored against the animal and the date, so the labelled set starts with the first scorer. | Designed for beef cattle first; dairy animals are the same models with their own scored pictures, later. Needs a few thousand scored pictures from different animals, angles, seasons and places, scored by someone who knows cattle: beyond what we fund internally. |
| Connectivity at the site | The demo's dip-tank option assumes satellite connectivity (section 5b); the development machine already runs on Starlink Mini and solar, which is the same arrangement a tank site would need. | | |

What leaves the country today, in one line: the text of a WhatsApp message and any photo sent to the line go through Meta and are read by Anthropic's model; Tonga text sent for reading passes through the translator's hosted machine. The records themselves, the photos as stored, the entries and the training log stay on the machine in Batoka. That map is what a data-protection registration describes before a pilot; the goal, as the models become local, is for the first line to shrink to Meta alone.

Note (7 Nov 2026): the Tonga translator sits on NLLB-200, released under a non-commercial licence. This service is not for profit for as long as it is used to promote smallholder cattle farming in Southern Province: no subscriptions, no charge, which is the use the licence allows. Any commercial use, by a processor for instance, is discussed separately, and would need its own model licence. Should any charge ever be introduced, the Tonga layer is retrained on a permissively licensed base; the data and the method carry over. Changes: v0, 6 Nov 2026, from the product spec, the programme concept and the demo as of this evening. v0.1, same night: self-hosted Supabase; three hardware options by funds, what we suggest, ownership and an SPV (5b); WhatsApp as one of the front doors. v0.2, 7 Nov: satellite connectivity at dip tanks and securing the site as a community asset. v0.3, 7 Nov evening: section 9, how this is built, in the open: the tools, the models in use and planned, the machine in Batoka, the licences, what leaves the country, and what stays with us.
