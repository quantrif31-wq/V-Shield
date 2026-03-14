import os

base = "Vietnam License Plate.v2i.yolov8"

for root, dirs, files in os.walk(base):
    for file in files:
        if file.endswith(".txt"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) > 0:
                    parts[0] = "0"
                new_lines.append(" ".join(parts))

            with open(path, "w") as f:
                f.write("\n".join(new_lines))

print("ALL LABELS FIXED TO CLASS 0")