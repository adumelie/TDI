import sys
import re
import matplotlib.pyplot as plt

def count_trees(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # Case-insensitive and plural-insensitive search for "Trees"
            tree_count = len(re.findall(r'\b[Tt]rees?\b', content, re.IGNORECASE))
            return tree_count
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return 0

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py file1 file2")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    tree_count_file1 = count_trees(file1_path)
    tree_count_file2 = count_trees(file2_path)

    labels = [file1_path.split("/")[-1], file2_path.split("/")[-1]]
    counts = [tree_count_file1, tree_count_file2]

    colors = ['blue', 'red']

    plt.bar(labels, counts, color=colors)
    plt.xlabel('Files')
    plt.ylabel('Occurrences of "Trees"')
    plt.title('Occurrences of "Trees" in texts (case and plural insensitive)')
    plt.savefig("TreesInTexts.png")
    plt.show()

if __name__ == "__main__":
    main()
