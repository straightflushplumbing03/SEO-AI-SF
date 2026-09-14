# Operations — running SFGE day to day

## Quick start (new machine)

```bash
git clone <sfge-engine-repo>
cd sfge-engine
cp config.example.yaml config.yaml
cp .env.example .env               # set GITHUB_TOKEN, SFGE_SITE_REPO
python3 scripts/init_db.py         # idempotent: creates tables if missing
python3 scripts/livecheck.py       # sanity: live site baseline healthy
```

No third-party Python packages are required. The engine is pure stlib + the site repo's own
`scripts/build.py` for page assembly.

## The daily loop

1. **Log completed jobs** (technician form / SMS / CSV) — `scripts/intake_job.py`.
   Privacy rules are enforced at this boundary: no addresses, no names, no exact prices.
2. **Generate case studies** — `scripts/gen_case_study.py --job-id N`.
   This clones the site repo to a temp worktree, writes the page + hub + sitemap entry,
   creates a branch `sfge/case-study-<city>-<service>-<id>`, commits, and pushes.
   It then attempts to open a GitHub PR with the diff for human review.
3. **Human reviews the PR** on GitHub (Cloudflare Pages preview will attach via CI),
   and merges only after checking the rendered page.
4. **After merge**, re-run `scripts/livecheck.py` to confirm no regression.

## Environment / secrets

All from `.env` (never committed):

| Variable | Purpose |
|---|---|
| `GITHUB_TOKEN` | Push branches + open PRs to the site repo |
| `SFGE_SITE_REPO` | `straightflushplumbing03/-Up2datewebsiteseo` |
| `SFGE_SITE_CLONE_URL` | optional override (local bare repo for testing) |
| `SFGE_PUSH_URL` | optional override for push URL (testing) |

## Rate limiting & quality gates

- **One page per job**, never batched-wordpress-style volume.
- The engine will **not** auto-throttle; the human gate is the merge step. Do not merge more
  than 2–5 case studies per day, and only when the jobs are real.
- Tier-2 (scoped, `needs_field_data`) pages carry an open opportunity to upgrade to Tier-1 the
  moment a real job lands in that city+service.

## Testing

```bash
python3 -m unittest discover -s tests -v
```

Runs 18 tests covering schema shape, canonical/og consistency, privacy redaction,
tier-1/tier-2 content rules, internal-link graph, and sitemap patching.

## Rollback

If a merged page is wrong: revert the PR in the site repo (git revert) and delete the
corresponding `content` row / mark it `publish_status='retracted'`. Because every page is a
standalone `.html` file plus a sitemap line and a hub card, reverting is a normal 3-file PR.