import requests
import os
import subprocess
import time
import re
import csv
from datasets import load_dataset

# ====================================
# CONFIG
# ====================================
#our Token:

# HuggingFace token loaded from environment variable
HF_TOKEN = os.environ.get("HF_TOKEN")

#Codellamma End Point

ENDPOINT = "https://dz7aqcj07ai4lw1f.us-east-1.aws.endpoints.huggingface.cloud"
API_URL = f"{ENDPOINT}/v1/chat/completions"

OUTPUT_DIR = "outputs/Codellama_AllPatches"
REPO_DIR = "repos"

os.makedirs(OUTPUT_DIR, exist_ok=True)

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

# ====================================
# TARGET BUGS
# ====================================

TARGET_BUGS = [
"django__django-12113",
"django__django-13791",
"django__django-11179",
"django__django-11405",
"django__django-11490",
"django__django-11695",
"pytest-dev__pytest-11143",
"pytest-dev__pytest-6116",
"pytest-dev__pytest-7521",
"pytest-dev__pytest-11148",
"pytest-dev__pytest-5227",
"pytest-dev__pytest-5555",
"psf__requests-1376",
"psf__requests-1921",
"psf__requests-1962",
"psf__requests-3718"
]

# ====================================
# LOAD DATASET
# ====================================

print("Loading SWE-bench dataset...")
dataset = load_dataset("princeton-nlp/SWE-bench", split="test")
bugs = [bug for bug in dataset if bug["instance_id"] in TARGET_BUGS]
print("Loaded bugs:", len(bugs))


# ====================================
# EXTRACT FILE FROM PATCH
# ====================================

def extract_bug_file(patch):

    for line in patch.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" ")
            return parts[2][2:]

    return None


# ====================================
# EXTRACT REMOVED LINES
# ====================================

def extract_removed_lines(patch):

    removed = []

    for line in patch.split("\n"):
        if line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:].strip())

    return removed[:3]


# ====================================
# LOCATE BUG LINE
# ====================================

def locate_bug_line(repo_name, file_path, commit, removed_lines):

    repo_path = os.path.join(REPO_DIR, repo_name)

    try:

        content = subprocess.check_output(
            ["git", "-C", repo_path, "show", f"{commit}:{file_path}"],
            text=True
        )

        lines = content.split("\n")

        for removed in removed_lines:

            for i, line in enumerate(lines):

                if removed.strip() in line:
                    return i + 1

        return None

    except:
        return None


# ====================================
# EXTRACT HUNK LINE (fallback)
# ====================================

def extract_bug_line(patch):

    for line in patch.split("\n"):

        if line.startswith("@@"):

            m = re.search(r"\+(\d+)", line)

            if m:
                return int(m.group(1))

    return None


# ====================================
# LOAD CODE WINDOW
# ====================================

def get_code_window(repo_name, file_path, commit, bug_line, radius=20):

    repo_path = os.path.join(REPO_DIR, repo_name)

    try:

        content = subprocess.check_output(
            ["git", "-C", repo_path, "show", f"{commit}:{file_path}"],
            text=True
        )

        lines = content.split("\n")

        start = max(0, bug_line - radius)
        end = min(len(lines), bug_line + radius)

        numbered = []

        for i in range(start, end):
            numbered.append(f"{i+1:5d}: {lines[i]}")

        return "\n".join(numbered)

    except:
        return ""


# ====================================
# CLEAN PATCH
# ====================================

def clean_patch(text):

    if "diff --git" not in text:
        return text

    idx = text.find("diff --git")
    text = text[idx:]

    parts = text.split("diff --git")

    return "diff --git" + parts[1]


# ====================================
# PATCH VALIDATION
# ====================================

def validate_patch(patch, file_path):

    if patch is None:
        return False

    if "diff --git" not in patch:
        return False

    if file_path not in patch:
        return False

    if "@@" not in patch:
        return False

    if "+" not in patch or "-" not in patch:
        return False

    return True


# ====================================
# BUILD PROMPT
# ====================================

def build_prompt(bug):

    repo_name = bug["repo"].split("/")[-1]

    file_path = extract_bug_file(bug["patch"])

    removed_lines = extract_removed_lines(bug["patch"])

    bug_line = locate_bug_line(
        repo_name,
        file_path,
        bug["base_commit"],
        removed_lines
    )

    if bug_line is None:
        bug_line = extract_bug_line(bug["patch"])

    code_window = get_code_window(
        repo_name,
        file_path,
        bug["base_commit"],
        bug_line
    )

    removed_block = "\n".join(removed_lines)

    prompt = f"""
You are fixing a real bug in a software repository.

Repository:
{bug["repo"]}

Bug description:
{bug["problem_statement"]}

File:
{file_path}

Buggy line:
{removed_block}

The bug occurs around line {bug_line}.

Code context:

{code_window}

Task:

Modify the buggy line to fix the bug.

Rules:

- modify at most 3 lines
- do not change other functions
- minimal patch only

Return ONLY a unified git diff patch.
"""

    return prompt, removed_lines, file_path


# ====================================
# CALL MODEL
# ====================================

def generate_patch(prompt):

    payload = {
        "model": "codellama",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.05,
        "max_tokens": 400
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        print("API error:", response.text)
        return None

    result = response.json()

    return clean_patch(result["choices"][0]["message"]["content"])


# ====================================
# RESULTS CSV
# ====================================

csv_file = open("patch_results.csv", "w", newline="", encoding="utf-8")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["instance_id", "status"])


# ====================================
# MAIN LOOP
# ====================================

for i, bug in enumerate(bugs):

    print("\nProcessing", i + 1, "/", len(bugs))

    prompt, removed_lines, file_path = build_prompt(bug)

    patch = generate_patch(prompt)

    valid = validate_patch(patch, file_path)

    status = "VALID" if valid else "INVALID"

    output_file = f"{OUTPUT_DIR}/{bug['instance_id']}.patch"

    with open(output_file, "w", encoding="utf-8") as f:

        f.write(f"# STATUS: {status}\n\n")

        if patch:
            f.write(patch)

    csv_writer.writerow([bug["instance_id"], status])

    print("Saved:", output_file, "|", status)

    time.sleep(2)

csv_file.close()

print("\nPatch generation complete")