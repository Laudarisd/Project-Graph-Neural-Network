import glob

# Define the float values to match
TARGET_VALUES = [20.0, 20.0, 15.0, 10.0, 0.0]
match_removed_total = 0
files_modified = 0

txt_files = glob.glob("./labels/*.txt")

for file_path in txt_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    matches_in_file = 0

    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5:
            try:
                last_five = list(map(float, parts[-5:]))
                if last_five == TARGET_VALUES:
                    matches_in_file += 1
                    continue  # skip this line
            except ValueError:
                pass  # skip problematic lines
        new_lines.append(line)

    if matches_in_file > 0:
        match_removed_total += matches_in_file
        files_modified += 1
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

print(f"\n✅ Removed {match_removed_total} matching lines from {files_modified} files.")
