# Rollback Runbook (§7)

1. **Identify the prior release tag.**

   ```bash
   git fetch --tags
   git tag --sort=-creatordate | head
   ```

2. **Checkout the previous release.**

   ```bash
   git checkout <previous-tag>
   ```

3. **Restore the matching index snapshot.**
   - Locate the snapshot in `indices/snapshots/` stamped with the release timestamp.
   - Copy it over the active index:

     ```bash
     cp indices/snapshots/<snapshot>.json indices/atticus_index.json
     ```

4. **Re-pin configuration.**
   - Verify `requirements.txt` and `package.json` match the target tag.
   - Confirm embedding/LLM identifiers (`text-embedding-3-large`, `gpt-4.1`) in `atticus/config.py`.
5. **Smoke test with gold queries.**

   ```bash
   pytest eval/harness -k retrieval --maxfail=1
   ```

   Review `eval/runs/YYYYMMDD/` outputs for the top queries (nDCG@10, Recall@50, MRR).

6. **Log the rollback.**
   - Append the action to `CHANGELOG.md`.
   - Tag the rollback release (e.g., `v0.1.0-rollback1`) with a short summary of the trigger and outcome.
