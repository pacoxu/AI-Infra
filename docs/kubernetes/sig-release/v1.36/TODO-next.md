# TODO For Next Steps (Not Executed In This PR)

This file is only for planning step 2 and step 3 after step 1 research.

## Step 2: English Blog Draft

1. Re-check upstream status on writing day:
- final release date confirmation
- final release blog/theme/logo links
- final `CHANGELOG-1.36.md` and release-notes changes

2. Draft EN blog based on `research.md`:
- executive summary
- major GA/Beta/Alpha highlights
- upgrade/deprecation risks
- references

3. Validate facts one more time before publish:
- KEP stage and target release still unchanged
- any newly disclosed known issue

## Step 3: Chinese Blog Draft

Status: completed in this branch.

Output:

- `kubernetes/sig-release/v1.36/release.md`

Also added:

- `AI-Infra` action-list sections in both drafts:
- `kubernetes/sig-release/v1.36/release.en.md`
- `kubernetes/sig-release/v1.36/release.md`

1. Translate with localization (not literal conversion):
- keep technical meaning exact
- adapt wording to domestic/private-cloud reader focus

2. Keep structure aligned with historical local posts:
- title + theme
- key highlights by stage
- upgrade notes and deprecations
- historical links and references

3. Final consistency checks:
- terminology consistency (EN/CN names)
- KEP links and release date consistency with EN version
