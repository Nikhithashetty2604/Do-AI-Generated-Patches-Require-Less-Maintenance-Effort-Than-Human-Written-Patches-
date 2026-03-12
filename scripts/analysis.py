from datasets import load_dataset
import git
import os
import csv

# -----------------------------
# Load SWE-bench dataset
# -----------------------------
DATASET = load_dataset("princeton-nlp/SWE-bench", split="test")

targets = ["django/django", "pytest-dev/pytest", "psf/requests"]

# keep only those repos
filtered = [x for x in DATASET if x["repo"] in targets]

# measure patch size
def patch_size(bug):
    return len(bug["patch"].split("\n"))

# split by repo and sort by smallest patches
django = sorted(
    [x for x in filtered if x["repo"] == "django/django"],
    key=patch_size
)

pytest = sorted(
    [x for x in filtered if x["repo"] == "pytest-dev/pytest"],
    key=patch_size
)

requests = sorted(
    [x for x in filtered if x["repo"] == "psf/requests"],
    key=patch_size
)

# pick the smallest patches
selected = django[:6] + pytest[:6] + requests[:4]

results = []
# -----------------------------
# Extract added lines from patch
# -----------------------------
def extract_added_lines(patch):
    added = []
    for line in patch.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    return added

# -----------------------------
# Extract modified file paths
# -----------------------------
def extract_files(patch):
    files = []
    for line in patch.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" ")
            files.append(parts[2][2:])
    return files

# -----------------------------
# Find commits modifying a line
# -----------------------------
def get_line_commits(repo, file_path, line_text, base_commit):
    try:
        commits = repo.git.log(
            "-S", line_text,
            "--pretty=format:%H",
            f"{base_commit}..HEAD",
            "--", file_path
        ).split("\n")

        commits = [c for c in commits if c.strip() != ""]
        return commits

    except Exception:
        return []

# -----------------------------
# Analyze a bug fix patch
# -----------------------------
def analyze_bug(bug):

    repo_name = bug["repo"].split("/")[-1]
    repo_path = os.path.join("repos", repo_name)

    repo = git.Repo(repo_path)

    base_commit = bug["base_commit"]
    base = repo.commit(base_commit)

    print("Processing:", bug["instance_id"])

    files = extract_files(bug["patch"])
    lines = extract_added_lines(bug["patch"])

    if not files:
        return

    file_path = files[0]

    all_commits = set()
    first_edit_days = []
    first_edit_commit = None

    for line in lines:

        commits = get_line_commits(repo, file_path, line, base_commit)

        if commits:

            all_commits.update(commits)

            for c in commits:

                commit_obj = repo.commit(c)

                if commit_obj.committed_datetime > base.committed_datetime:

                    days = (
                        commit_obj.committed_datetime
                        - base.committed_datetime
                    ).days

                    first_commit = commit_obj
                    first_edit_days.append(days)

                    if (
                        first_edit_commit is None
                        or first_commit.committed_datetime
                        < repo.commit(first_edit_commit).committed_datetime
                    ):
                        first_edit_commit = c

                    break


    # Metrics
    d1 = len(all_commits)
    d2 = min(first_edit_days) if first_edit_days else None

    commit_list = ";".join(all_commits)

    results.append({
        "bug": bug["instance_id"],
        "repo": repo_name,
        "d1_followup_commits": d1,
        "d2_days_to_first_edit": d2,
        "first_edit_commit": first_edit_commit,
        "all_edit_commits": commit_list
    })

# -----------------------------
# Run analysis
# -----------------------------
for bug in selected:
    analyze_bug(bug)

# -----------------------------
# Save results
# -----------------------------
os.makedirs("outputs", exist_ok=True)

with open("outputs/Human_bug_metrics.csv", "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "bug",
            "repo",
            "d1_followup_commits",
            "d2_days_to_first_edit",
            "first_edit_commit",
            "all_edit_commits"
        ]
    )

    writer.writeheader()
    writer.writerows(results)

print("Results written to outputs/Human_bug_metrics.csv")