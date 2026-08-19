# Launching vectorspace.pk on GitHub Pages

Follow these in order. Steps 1–3 get the site live on a GitHub address; steps 4–6 put it on your own domain. Budget about 40 minutes, plus waiting time for DNS.

---

## Before you start

Two things to have open:

- A **GitHub account** — free, at github.com
- Your **domain registrar** account, wherever you bought `vectorspace.pk`

And install **GitHub Desktop** (desktop.github.com). It's free, and it means you never touch a terminal.

---

## 1. Create the repository and push

1. Open **GitHub Desktop** → sign in
2. **File → Add Local Repository** → choose `~/Downloads/files 3/vectorspace`
3. It will say the folder isn't a git repository and offer to **create one**. Accept.
4. In the box on the left, type a summary like `Initial site` and click **Commit to main**
5. Click **Publish repository** at the top
   - Name it something like `vectorspace`
   - **Uncheck "Keep this code private"** — GitHub Pages needs a public repo on the free plan
   - Click **Publish**

**The first push is about 282 MB, almost all past papers.** It will take a while depending on your connection. Leave it running; it only happens once.

### What gets uploaded

Everything except `docs/`, which is deliberately excluded — GitHub rebuilds it on their servers. So the repo contains `build.py`, `content/`, `static/`, `templates/`, `.github/`, and the README files.

---

## 2. Turn on GitHub Pages

In your repository on github.com:

**Settings → Pages** (left sidebar)

Under **Build and deployment → Source**, choose **GitHub Actions**.

**This is the step people get wrong.** Do not choose "Deploy from a branch" — this site is built by a workflow, not served from a folder, and the branch option will publish nothing.

You don't need to pick a workflow. The one at `.github/workflows/deploy.yml` is already in your repo and GitHub will find it.

---

## 3. Watch the first build

Go to the **Actions** tab. You should see a run called *Build and deploy site* in progress.

- **Green tick** — the site is live. Click into the run and the deploy step shows the URL, something like `https://yourname.github.io/vectorspace/`
- **Red X** — click the run to see the error, and send me the message. It'll be something small.

The first run takes a few minutes because of the PDFs. Later ones are quicker.

**Check the site works at that GitHub address before doing anything with your domain.** Click through a topic page, open a PDF, open a dropdown.

---

## 4. Point your domain at GitHub

Log in to your registrar and find the DNS settings for `vectorspace.pk`. Add these records.

**For www.vectorspace.pk** — this is the one that matters, since it's what the site is configured for:

| Type | Name / Host | Value |
|---|---|---|
| CNAME | `www` | `yourname.github.io` |

Replace `yourname` with your GitHub username. Keep the trailing dot if your registrar adds one.

**For vectorspace.pk without the www** — so the bare domain redirects to the www one, add all four:

| Type | Name / Host | Value |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |

Some registrars write the host as `@`, some leave it blank, some want the full domain. All three mean the same thing.

DNS changes usually take 15–60 minutes, occasionally longer.

---

## 5. Tell GitHub about the domain

Back in **Settings → Pages**:

1. Under **Custom domain**, enter `www.vectorspace.pk` and click **Save**
2. GitHub runs a DNS check. It may say "domain's DNS record could not be verified" for a while — that's normal while DNS propagates. Come back in an hour.
3. Once it verifies, tick **Enforce HTTPS**

The certificate takes a few minutes to issue after that. Until it does you may see a security warning — that's expected and it resolves itself.

**One thing to know:** your repo already contains a `CNAME` file (the build writes it from the `domain:` line in `content/site.txt`). If you ever change the domain, change it there, not on GitHub — otherwise the next build will overwrite GitHub's setting.

---

## 6. After it's live

- Open the site on your phone, on mobile data, not wifi
- Send yourself the link on WhatsApp and check the preview image appears
- Verify at **Google Search Console** and submit `https://www.vectorspace.pk/sitemap.xml`
- Put the link in your Instagram bio

---

## Publishing changes from then on

Edit a file in `content/`, then in GitHub Desktop: type a summary, **Commit to main**, **Push origin**. About a minute later the site has updated.

Or edit directly on github.com — click a file, the pencil icon, **Commit changes**. Same result, works from your phone.

**Before asking me to make changes, click Fetch/Pull in GitHub Desktop first** — that brings down anything you edited in the browser, so we don't end up with two versions of the same file.

---

## Still outstanding

Small things worth doing, none of which block launch:

- **The Formspree form** — there isn't one any more. Registration goes to your Google Form and questions go to WhatsApp, so nothing to set up.
- **A share image** at `static/img/og-default.png` exists and works, but it's the generic one I generated. Replace it whenever you want something better.
- **The polar grid PDF** renders heavy on screen because of its hairline widths. Fine in print. Say the word and I'll thicken the strokes.

---

## If something goes wrong

**Build fails** — Actions tab, click the red run, read the last lines. Paste them to me.

**Site is live but looks unstyled** — usually the Pages source is set to a branch instead of GitHub Actions. Recheck step 2.

**Domain shows a 404 or the wrong site** — the CNAME record is probably pointing somewhere else, or hasn't propagated. Wait an hour and recheck.

**A change doesn't appear** — hard-refresh with `Cmd + Shift + R`. Pages are cached by your browser; the stylesheet is version-stamped but the HTML isn't.
