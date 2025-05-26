import glob

# Define target as floats for robust comparison
TARGET_VALUES = [20.0, 20.0, 15.0, 10.0, 0.0]

target_count_eq_1 = 0
target_count_gt_1 = 0
files_with_gt_1 = []

txt_files = glob.glob("./labels/*.txt")

for file_path in txt_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    match_count = 0
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5:
            try:
                last_five = list(map(float, parts[-5:]))
                if last_five == TARGET_VALUES:
                    match_count += 1
            except ValueError:
                continue  # skip lines with unexpected formatting

    if match_count == 1:
        target_count_eq_1 += 1
    elif match_count > 1:
        target_count_gt_1 += 1
        files_with_gt_1.append((file_path, match_count))

# Print summary
target_str = " ".join(map(str, TARGET_VALUES))
print(f"Total number of files with exactly 1 match of {target_str}: {target_count_eq_1}")
print(f"Total number of files with more than 1 match of {target_str}: {target_count_gt_1}")

if files_with_gt_1:
    print("\nFiles with more than 1 match:")
    for path, count in files_with_gt_1:
        print(f"- {path} ({count} matches)")
else:
    print("\n(No files with more than 1 match found.)")
