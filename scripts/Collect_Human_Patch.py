from datasets import load_dataset
import os

# --------------------------------
# The 16 Bugs
# -------------------------------
BUG_IDS = [
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


# --------------------------------
# Load SWE-bench dataset
# --------------------------------
print("Loading SWE-bench dataset...")
dataset = load_dataset("princeton-nlp/SWE-bench", split="test")

# --------------------------------
# Filter dataset to only our bugs
# --------------------------------
selected_bugs = [
    bug for bug in dataset
    if bug["instance_id"] in BUG_IDS
]

print(f"Found {len(selected_bugs)} matching bugs")

# --------------------------------
# Create directory for patches
# --------------------------------
PATCH_DIR = "../data/patches/human"
os.makedirs(PATCH_DIR, exist_ok=True)

# --------------------------------
# Save human patches
# --------------------------------
for bug in selected_bugs:

    instance_id = bug["instance_id"]
    patch_text = bug["patch"]

    patch_file = os.path.join(
        PATCH_DIR,
        f"{instance_id}.patch"
    )

    with open(patch_file, "w", encoding="utf-8") as f:
        f.write(patch_text)

    print("Saved:", patch_file)

print("\nAll human patches saved successfully.")