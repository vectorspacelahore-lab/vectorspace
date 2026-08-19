# Vector Space — how this website works

Everything you need to run and change **www.vectorspace.pk**, written for someone who doesn't code.

You never edit HTML. You edit plain text files in `content/`, and a small program turns them into the finished website. That program is `build.py`, it uses nothing but what already comes with Python, and you will rarely need to open it.

---

## Contents

1. [The five-minute version](#1-the-five-minute-version)
2. [How the folders are laid out](#2-how-the-folders-are-laid-out)
3. [The content file format](#3-the-content-file-format)
4. [Adding a new topic](#4-adding-a-new-topic)
5. [Adding videos, notes, worksheets and papers](#5-adding-videos-notes-worksheets-and-papers)
6. [Adding a whole new subject](#6-adding-a-whole-new-subject)
7. [Editing the home, about and contact pages](#7-editing-the-home-about-and-contact-pages)
8. [Publishing changes](#9-publishing-changes)
9. [Changing how it looks](#10-changing-how-it-looks)
10. [Naming files — read this before uploading anything](#11-naming-files--read-this-before-uploading-anything)
11. [When something breaks](#12-when-something-breaks)
12. [Things to do before launch](#13-things-to-do-before-launch)
13. [Where the limits are](#14-where-the-limits-are)
14. [Courses and registration](#15-courses-and-registration--no-forms-anywhere)
15. [Repository size](#16-repository-size--read-this-before-you-add-much-more)

---

## 1. The five-minute version

**To change something on the site:** find the file in `content/`, edit the text, save, push to GitHub. The site updates itself about a minute later.

**To see your change before anyone else does**, open Terminal, go to this folder and run:

```
python3 build.py
python3 -m http.server -d docs 8000
```

Then open `http://localhost:8000` in your browser. Press `Ctrl+C` in Terminal to stop.

That's the whole workflow. Everything below is detail.

---

## 2. How the folders are laid out

```
vectorspace/
├── content/            ← YOU EDIT THINGS IN HERE
│   ├── site.txt              settings, subjects, papers
│   ├── pages/                home, about, contact, courses, privacy
│   └── further-maths/        one folder per subject
│       └── further-pure-1/     one folder per paper
│           └── matrices.txt      one file per topic = one page
│
├── static/             ← YOU PUT FILES IN HERE
│   ├── assets/site.css       all the styling
│   ├── notes/                your revision notes PDFs
│   ├── worksheets/           your worksheets and answers
│   ├── solutions/            your worked solutions
│   ├── papers/               past papers and mark schemes
│   └── img/                  favicon and share image
│
├── templates/
│   └── base.html             the page layout — nav, footer, meta tags
│
├── build.py            the program. You shouldn't need to touch it.
├── docs/               the finished website. Never edit — it gets deleted
│                       and rebuilt every time you run build.py.
└── README.md           this file
```

**The one rule:** anything you put inside `static/` appears on the live site at the same path. A file at `static/notes/matrices.pdf` is reachable at `www.vectorspace.pk/notes/matrices.pdf`.

---

## 2a. Nothing is ever a dead link

This is worth understanding before you add anything, because it changes how you work.

**You can name a PDF in a content file before you've made it.** When the site is built it checks whether each file actually exists in `static/`. If it doesn't, that row shows a **Coming soon** tag instead of a link that would 404.

So you can list all ten years of past papers today, upload them over the next six months, and the site is correct and complete-looking at every point in between. No student ever taps a broken link.

Every time you build, the terminal tells you exactly which files are still missing:

```
82 file(s) named in your content but not yet in static/.
These show as 'Coming soon' on the site — nothing is broken.
   · notes/9231-fp1-matrices-notes.pdf
   · papers/9231-s24-qp-11.pdf
   …
```

That list is your to-do list. When it's empty, everything you've promised is live.

The same applies at page level: unwritten topics show a Coming soon panel, the resources page says so while it's empty, and the 404 page does too.

---

## 3. The content file format

Every content file is split into **sections**. A section starts with its name between three equals signs:

```
=== meta ===
title: Matrices

=== intro ===
A matrix is a way of writing down a transformation…
```

Three things to know:

- **Lines starting with `#` are ignored.** Use them to leave yourself notes. Every file already has plenty.
- **Delete a whole section and it simply disappears from the page.** No FAQ section means no FAQ block. Nothing breaks.
- **Sections come in three shapes**, and each one tells you what to type:

| Shape | Looks like | Used for |
|---|---|---|
| Settings | `title: Matrices` | `meta`, course details |
| Lists | `- point one` | syllabus, mistakes, tips |
| Tables | `Label \| filename` | videos, notes, papers |

For the table shape, the `|` character separates the columns. It's above the backslash on most keyboards. Spaces around it don't matter.

**Writing prose.** In `intro` and `body` sections you can use:

- a blank line to start a new paragraph
- `**double stars**` for **bold**
- `*single stars*` for *italics*
- `## Two hashes` for a section heading
- `[words](/some-page/)` for a link
- `{highlight}words{/highlight}` for the yellow block behind text

---

## 4. Adding a new topic

Say you want to add **Polar Coordinates** to Further Pure 1.

**Step 1.** Copy `content/further-maths/further-pure-1/matrices.txt` and rename the copy `polar-coordinates.txt`.

The filename becomes the web address, so keep it lowercase with hyphens and no spaces. This file becomes `www.vectorspace.pk/further-maths/further-pure-1/polar-coordinates/`.

**Step 2.** Open it and change the `meta` section:

```
=== meta ===
title: Polar Coordinates
order: 5
description: Polar coordinates for CIE Further Pure 1 (9231) — lecture videos, notes and worked solutions.
```

- `title` — what appears as the heading and in the menu.
- `order` — where it sits in the list. Lower numbers come first. It doesn't have to be exact; the numbers are only used for sorting, and the site renumbers the cards 01, 02, 03 automatically.
- `description` — the sentence Google shows under your link, and what appears when someone shares it on WhatsApp. Aim for about 20 words, and mention the topic and the syllabus code.

**Step 3.** Replace the rest of the content. Delete any section you don't have yet.

### Marking a topic "coming soon"

All 74 topics across the three live subjects already exist as files, each with a written description, syllabus points and common mistakes. None of them is marked "soon" any more — they have real content, and their PDFs show as Coming soon until you upload them.

If you ever want to hide a topic's content, add this line to its `meta` section:

```
status: soon
```

While that line is there, the page shows a **Coming soon** panel pointing people at your Instagram, and **everything else in the file is ignored**. That's deliberate — it means a half-finished file can sit in the repo with placeholder text in it and none of that text can ever reach the site.

The topic still gets a card on its paper page, marked with a dashed border and a small "Soon" tag, so students can see what's coming.

**To publish a topic: delete the `status: soon` line**, fill in the sections, and rebuild. That one line is the whole switch.

**Step 4.** Publish (see section 9). The topic appears automatically on the Further Pure 1 page, on the Further Maths page, in the sitemap and in the resources list. **You never add it to a menu by hand.**

---

## 5. Adding videos, notes, worksheets and papers

### Videos — not on the site yet, but ready when you are

No topic page currently has lecture videos. Every page has a description, the syllabus points, worksheets, topical past papers, worked solutions and common mistakes.

**The video machinery is still there.** When you have a recording, add a section like this to any topic file and the videos appear above the notes:

```
=== videos ===
Part 1 — What a matrix actually is | dQw4w9WgXcQ
Part 2 — Determinants and inverses | aBc123XyZ_9
```

The bit after the `|` is the **YouTube video ID**. Open the video on YouTube and look at the address bar:

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
                                ^^^^^^^^^^^ this is the ID
```

Copy everything after `v=`. Unlisted videos work fine. A reminder of this is already commented at the top of every topic file.

**Why videos don't load until tapped.** Each YouTube player is over a megabyte. Three of them on a page is a slow, expensive load for a student on mobile data. So the site shows the thumbnail and only loads the real player when they tap it. Nothing for you to do — it just works.

### Notes, worksheets, topical papers and solutions

Four sections, all the same shape — `Label | filename`:

Every topic page runs in the same order: **introduction, syllabus points, common mistakes**, then the downloads. The teaching comes first; the files come after.

There are two download blocks, and each carries a line telling the student when to use it.

| Section | Heading on the page | Default folder |
|---|---|---|
| `=== notes ===` | Lecture notes | `static/notes/` |
| `=== worksheets ===` | Worksheets | `static/worksheets/` |
| `=== topical ===` | Topical past papers | `static/papers/` |

All 74 topics look like this:

```
=== worksheets ===
Practice worksheet | 9231-fp1-matrices-worksheet.pdf
Worksheet answers | 9231-fp1-matrices-answers.pdf
Step-by-step solutions | 9231-fp1-matrices-worksheet-solutions.pdf | solutions

=== topical ===
Topical questions | 9231-fp1-matrices-topical.pdf
Mark scheme | 9231-fp1-matrices-topical-ms.pdf
Step-by-step worked solutions | 9231-fp1-matrices-worked-solutions.pdf | solutions
```

**Note the optional third column.** Writing `| solutions` at the end of a row tells the site that file lives in `static/solutions/` rather than the block's default folder. That's how the step-by-step solutions sit inside the Worksheets and Topical blocks while their PDFs stay filed with your other solutions.

There is no longer a separate "Worked solutions" heading — solutions belong beside the questions they answer.

```
=== notes ===
Lecture notes | 9231-fp1-matrices-notes.pdf
```

Write **only the filename**, not the whole path. Add as many lines as you like under each, or delete the whole section if you don't have those files yet.

### One-off extras — a printable grid, a formula card, anything else

Some topics need a resource that isn't a worksheet or a past paper. Add an `extra` block and give it its own heading and explanation:

```
=== extra ===
> Trouble sketching polar curves?
Print this out and sketch straight onto it. Once the grid feels familiar you
can sketch these curves on plain paper without it.
Polar grid paper | 9231-fp1-polar-coordinates-grid.pdf | notes
```

The line starting with `>` is the heading. The plain line under it is the explanation shown beneath it. Then the usual `Label | filename | folder` rows — the folder defaults to `notes` if you leave it off.

You can add several blocks to one topic, each with its own `>` heading. Polar Coordinates uses this for its printable radial grid.

### Whole past papers

Yearly papers do **not** go on topic pages — they'd be repeated on every one. They live on the subject's past papers page instead, and each topic page automatically shows a link across to it. See section 6a.

---

## 6a. The past papers page

Each subject can have one, at `/further-maths/past-papers/`. It's built from a file named **exactly** `past-papers.txt` sitting directly inside the subject folder:

```
content/further-maths/past-papers.txt
```

That exact filename is special — the site treats it as the past papers page rather than as a topic, gives it a card on the subject page, and adds a link to it from every topic page in that subject. To give Add Maths one, copy the file to `content/add-maths/past-papers.txt` and edit it.

It has two sections.

**Topical** — every past question on one topic, in one file, grouped into a dropdown per paper. A line starting with `>` opens a new dropdown:

```
=== topical ===
> Paper 1 — Further Pure Mathematics 1
1.4 Matrices | 9231-fp1-matrices-topical.pdf | 9231-fp1-matrices-topical-ms.pdf | 9231-fp1-matrices-worked-solutions.pdf

> Paper 2 — Further Pure Mathematics 2
2.1 Hyperbolic functions | …
```

Each row has **four** parts: topic name, questions file, mark scheme file, worked solutions file.

- Questions and mark schemes go in `static/papers/`
- Your own worked solutions go in `static/solutions/`
- Leave any of the three filenames blank and that link shows Coming soon

All 24 Further Maths topics are listed and their questions and mark schemes are uploaded. The dropdown header shows how many of its topics are ready, so students can see progress at a glance.

**Yearly** — whole papers, grouped into a dropdown per **session**. A line starting with `>` opens a new one:

```
=== yearly ===
> Oct/Nov 2025
11 | 9231-w25-qp-11.pdf | 9231-w25-ms-11.pdf | 9231-w25-solved-11.pdf
12 | 9231-w25-qp-12.pdf | 9231-w25-ms-12.pdf | 9231-w25-solved-12.pdf

> May/June 2025
11 | 9231-s25-qp-11.pdf | …

> Feb/March 2025
12 | 9709-m25-qp-12.pdf | …
```

Each row is variant, question paper, mark scheme, **solved paper**. The session is the dropdown heading, so it isn't repeated on every row. Newest session first. Question papers and mark schemes go in `static/papers/`; your solved papers go in `static/solutions/`.

All three subjects are loaded with **2020 to 2025**: 152 Further Maths papers across 12 sessions, 220 A Level Maths across 18 (it has a Feb/March sitting), and 50 Add Maths across 12. Questions and mark schemes are live; the solved-paper column is waiting on your worked solutions.

The filename pattern is `{code}-{session}-{qp|ms|solved}-{variant}.pdf`, where session is `s` for May/June, `w` for Oct/Nov and `m` for Feb/March, followed by the two-digit year — so `9709-m25-qp-12.pdf` is the Feb/March 2025 paper 12.

---

## 6. Adding a whole new subject

Subjects are listed in `content/site.txt`:

```
=== subjects ===
further-maths | Further Mathematics | 9231 | A Level | Σ | live | Four papers…
a-level-maths | Mathematics | 9709 | A Level | ∂ | soon | Pure, mechanics…
```

The columns are: **folder name | display name | syllabus codes | level | decorative symbol | status | one-line description**.

`status` does the work:

- `live` — appears in the menu, and as a full card on the home page
- `soon` — kept out of the menu, and shown on the home page as a **greyed-out card marked Coming soon**, so students can see what's planned

Three subjects are live (Further Maths, A Level Maths, Add Maths) and **O Level Mathematics is set to `soon`**. To launch it:

1. Change its status from `soon` to `live` in `site.txt`
2. Make a folder `content/a-level-maths/`
3. If the subject splits into papers, add them under `=== papers ===` in `site.txt` and make a folder per paper
4. Add topic files

The papers list has five columns:

```
=== papers ===
further-maths | further-pure-1 | Paper 1 | Further Pure Mathematics 1 | Roots and coefficients…
```

**folder name | web address | small yellow tag | full name | one-line description**

Write the tag out in full — `Paper 1`, `Paper 3` — exactly as you want it to appear. It's shown as-is, so every paper reads identically no matter what it's called.

### Choosing how a subject's papers are shown

Underneath the papers list in `site.txt` is a short `layouts` block:

```
=== layouts ===
further-maths | cards
a-level-maths | dropdowns
```

- **`cards`** — a grid of cards, one per paper, each linking to its own page. Further Maths uses this.
- **`dropdowns`** — one dropdown per paper with its chapters listed inside, so everything is visible from the subject page without clicking through. A Level Maths uses this.

Swap the word on either line to switch that subject over — nothing else changes, and both layouts use the same content files. A subject with no papers at all, like Add Maths, always shows a plain grid of chapters.

### Where past papers appear

Any subject with a `past-papers.txt` file automatically gets a dark band at the foot of its subject page linking through, and a line on every one of its topic pages pointing to it. All three live subjects have one.

If a subject has no papers, put the topic files straight in the subject folder and the site lists them as one grid — that's how Add Maths will work.

---

## 7. Editing the home, about and contact pages

All in `content/pages/`.

**`home.txt`** — the headline, the three steps, the About paragraph. Most visitors arrive here from your Instagram bio on a phone, so keep the headline short.

**`about.txt`** — the most important page on the site for trust.

At the top is the **portrait card**, laid out like your Instagram post: photo, then a headline with the opening words highlighted in yellow, then the standfirst and the student count.

```
=== card ===
photo: /img/ali-hashir.jpg
headline: {highlight}Ten years{/highlight} at the board
lede: I've spent the last decade teaching Cambridge Mathematics…
stat: **1000+** students taught so far
```

To change the photo, put a new file in `static/img/` and change the filename. Portrait shape works best — roughly 4 wide by 5 tall. The site converts it to black and white in the browser, so you can upload the colour original.

Below the card, the page still has **two placeholders in [SQUARE BRACKETS]**: your qualifications and where you've taught. I deliberately left those blank rather than invent them. This is the page a parent checks before enrolling their child, and invented credentials there would be far worse than none.

**`contact.txt`** — the wording only. Your email, WhatsApp number and Instagram link all come from `site.txt`, so you change them in one place and they update on every page.

---

## 8. Courses and the enquiry form

Courses live in `content/pages/courses.txt`. Each one is a block, separated by a line containing only `---`.

Move a course between the three sections of the page by changing one line:

| `status:` | Where it appears |
|---|---|
| `open` | "Open for enrolment", with a Register button |
| `soon` | "Announced — not open yet", with a Register button |
| `past` | "Previously run" — quiet proof you actually run these |

The first course marked `open` or `soon` also appears as a band on the home page. **If no course is open or announced, that band disappears automatically** — the site reads correctly whether or not you're running something.

### Making the form actually deliver

Right now the form looks fine but goes nowhere. It's a static website, so it can't send email by itself. Fix it in five minutes:

1. Go to **formspree.io** and make a free account
2. Create a form — it gives you an address like `https://formspree.io/f/abcdwxyz`
3. Open `build.py`, search for `YOUR_FORM_ID`, and replace that whole address with yours
4. Publish, then test it on yourself

Until you've done that, students can still reach you by WhatsApp and email.

---

## 9. Publishing changes

### The easy way — no Terminal, works from your phone

1. Go to your repository on **github.com**
2. Click into the file you want to change
3. Click the pencil icon, edit, then **Commit changes**
4. Wait about a minute. The site is live.

A robot on GitHub runs `build.py` for you and publishes the result. You can watch it under the **Actions** tab. If it fails you'll get an email.

To upload PDFs this way: open `static/notes/` on GitHub, click **Add file → Upload files**, drag them in, commit. Note the browser limits you to **25 MB per file**, which is far more than any PDF you'll have.

### The local way — when you want to see it first

```
python3 build.py
python3 -m http.server -d docs 8000
```

Open `http://localhost:8000`. When it looks right, commit and push as normal.

Always preview locally before a big change. It costs ten seconds and catches typos.

---

## 10. Changing how it looks

**Colours, spacing and fonts** live at the top of `static/assets/site.css`, in the block marked `:root`. Change a value there and it updates on every page at once.

```
--ink:  #0E0F0D    type, the hero band, the footer
--bone: #F2F3EE    the page background
--acid: #EFCC1D    the one accent colour
```

The design rules, from your brand guide: three colours only, square corners, everything aligned left, no gradients or glows, all maths and numbers in JetBrains Mono.

**The page layout** — nav bar, footer, meta tags — is `templates/base.html`. The `{{ DOUBLE BRACE }}` slots get filled in by `build.py`. Edit the HTML around them freely, but don't rename or delete a slot.

**The yellow highlight** behind words in a headline: wrap them in `{highlight}like this{/highlight}`. Use it on one phrase per page.

---

## 11. Naming files — read this before uploading anything

Get this right the first time, because **renaming a file breaks the link for every student who bookmarked it or saved it in a WhatsApp group.**

The convention already in use:

```
Past papers      9231-s24-qp-11.pdf        code, session, type, variant
Mark schemes     9231-s24-ms-11.pdf
Your notes       9231-fp1-matrices-notes.pdf
Worksheets       9231-fp1-matrices-worksheet.pdf
Answers          9231-fp1-matrices-answers.pdf
Solutions        9231-fp1-matrices-worked-solutions.pdf
```

Sessions are `s` for May/June and `w` for October/November, then the two-digit year: `s24`, `w23`. This matches how students already talk about papers, so the addresses are guessable.

Always lowercase, always hyphens, never spaces, never capitals.

---

## 12. When something breaks

**The build stops with a red error.** Read the last line — it names the file and the line number. Nearly always one of:

- a missing `|` in a table row
- a section header typed as `== name ==` instead of `=== name ===`
- a colon missing after a setting name

**A topic doesn't appear.** Check the file is inside the right paper folder, ends in `.txt`, and that the paper is listed under `=== papers ===` in `site.txt`. The build prints a warning naming any file it skipped.

**A download says "Coming soon" when the file exists.** The filename in the content file doesn't exactly match the file in `static/` — capitals and hyphens must match precisely. The build's missing-file list shows the name it was looking for, so compare that against what's actually in the folder.

**The site didn't update after pushing.** Open the **Actions** tab on GitHub. A red X means the build failed and the error is inside. A green tick means it published — try a hard refresh (`Cmd+Shift+R`).

**You've broken something and want to undo it.** Every change is saved forever in GitHub's history. Open the file, click **History**, find the version from before, and restore it.

---

## 13. Things to do before launch

- [ ] Fill in the two `[SQUARE BRACKET]` placeholders in `content/pages/about.txt`
- [ ] Set your real `email` and `whatsapp` number in `content/site.txt`
- [ ] Add your `whatsapp_channel` link in `site.txt` if you have one
- [ ] Connect the form to Formspree (section 8)
- [ ] Fill in real dates, fees and schedules in `content/pages/courses.txt`
- [ ] Point the `vectorspace.pk` domain at GitHub Pages, and turn on **Enforce HTTPS** in repository Settings → Pages
- [ ] Verify the site in **Google Search Console** and submit `sitemap.xml`
- [ ] Test on your own phone, on mobile data, not wifi
- [ ] Send yourself the link on WhatsApp and check the preview image looks right

---

## 14. Where the limits are

GitHub Pages publishes sites up to **1 GB**, allows about **100 GB of downloads a month**, and caps a single file at **100 MB** (25 MB if you upload through the browser).

Your own material — notes, worksheets and solutions for every topic across every subject — comes to roughly **120 MB**. That fits comfortably and always will.

The only thing that can break this is trying to mirror the entire CIE past-paper archive for every syllabus, which runs to several gigabytes. So **add papers as you publish topics**, not all at once.

**Watch for one signal:** when the repository passes roughly 300 MB, or a deploy starts taking noticeably longer, it's time to move `static/papers/` to its own repository on a subdomain. That's a small job and nothing breaks if it's done properly with redirects.

---

## 15. Courses and registration — no forms anywhere

There is **no form on this website**. Every "Register" button opens WhatsApp with a message already typed in, addressed to the number in `content/site.txt`.

That was a deliberate choice: a static site can't send email by itself, form services need accounts and cost money once you get any volume, and your students are on WhatsApp anyway.

Courses live in `content/pages/courses.txt`, one block each, separated by a line of three dashes. The fields are:

```
name: A Level Mathematics
syllabus: CIE 9709
status: open
starts: 14 September
exam: May/June 2027
format: Online, live on Zoom · recordings provided
duration: 7 months, past-paper session included
schedule: To be announced — 4 classes per week, evenings
fee: Rs 10,000 per month
summary: One or two sentences about what the course covers.
```

Change `status` to move a course between "Open for enrolment", "Announced — not open yet" and "Previously run". Delete a field entirely and that row simply doesn't appear.

**The home page course band is generic.** It counts how many courses are open or announced and links to the courses page — it never names one. So when you change the courses, the home page follows automatically and you don't have to remember to update it.

If no course is open or announced, the band disappears from the home page entirely.

### One thing to check before you publish

The AS Level Mathematics fee is currently `[CONFIRM FEE — Rs 10,000 per month?]`. You gave me fees for Further Maths, A Level Maths and Add Maths but not AS Level, and I didn't want to invent a price you'd be committing to. Replace that line before the site goes live.

---

## 16. Repository size — read this before you add much more

The site is currently about **400 MB**, almost all of it past-paper PDFs (892 files).

That works. GitHub Pages publishes sites up to 1 GB and allows roughly 100 GB of downloads a month, so there is real headroom. But it's past the point where things stay effortless, so it's worth knowing what to expect:

- **The first push will be slow.** You're uploading 400 MB. Leave it running.
- **Each deploy takes a few minutes** rather than under one, because the whole site is packaged and republished every time.
- **Anyone cloning the repo downloads 400 MB**, including you if you ever set it up on a second computer.

**What would push it over.** Adding topical papers for A Level Maths and Add Maths, plus your own notes, worksheets and solved papers for all 74 topics, would plausibly add another 300–500 MB. That's when it stops being comfortable.

**The fix when you get there**, and it's not urgent: move `static/papers/` into its own repository published at `papers.vectorspace.pk`, and point the filenames at that subdomain. The teaching site drops back to well under 100 MB and stays fast, while the archive lives separately. It's a contained job and no existing link needs to break if it's done with redirects.

Until then, nothing needs doing. Just don't add another few hundred megabytes without thinking about it.


---

## 17. Dropdowns

Every dropdown on the site — the topical papers, the yearly sessions, the FAQ blocks — starts **closed** when a page loads. Students see the full list of what's available and open only what they want, rather than scrolling past one expanded section to reach the rest.

They're built with the browser's own `<details>` element, so they need no JavaScript, work with a keyboard, and are read correctly by screen readers.

If you ever want one open by default, add the word `open` to its tag in `build.py`:

```
<details class="paper-drop" open>
```
