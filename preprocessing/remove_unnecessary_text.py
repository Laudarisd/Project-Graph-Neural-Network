from pathlib import Path

# Directories to process
label_dirs = [
    Path("./train_dataset/train/labels"),
    Path("./train_dataset/valid/labels"),
    Path("./train_dataset/test/labels")
]

fixed_count = 0

for label_dir in label_dirs:
    if not label_dir.exists():
        continue

    for txt_file in label_dir.glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            continue

        # Check if first line is not numeric (e.g., 'YOLO_OBB')
        first_line = lines[0].strip()
        if not first_line or not first_line[0].isdigit():
            numeric_lines = [line for line in lines if line.strip() and line.strip()[0].isdigit()]
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.writelines(numeric_lines)
            fixed_count += 1

print(f"\n Removed non-numeric headers from {fixed_count} label file(s).")
