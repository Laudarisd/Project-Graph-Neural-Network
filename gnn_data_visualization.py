import csv
import matplotlib.pyplot as plt

def visualize_csv(csv_file):
    points = []
    lines = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            start_x = float(row["Start X"])
            start_y = float(row["Start Y"])
            end_x = float(row["End X"])
            end_y = float(row["End Y"])
            points.append((start_x, start_y))
            points.append((end_x, end_y))
            lines.append(((start_x, start_y), (end_x, end_y)))

    # Remove duplicate points
    unique_points = list(set(points))

    # Create the plot
    fig, ax = plt.subplots()
    
    # Plot points
    for point in unique_points:
        ax.plot(point[0], point[1], 'bo')  # 'bo' stands for blue color and circle marker

    # Plot lines
    for line in lines:
        (start_x, start_y), (end_x, end_y) = line
        ax.plot([start_x, end_x], [start_y, end_y], 'k-')  # 'k-' stands for black color and solid line

    # Set plot limits
    ax.set_xlim(0, 1024)
    ax.set_ylim(0, 846)
    ax.invert_yaxis()  # Invert y-axis to match the image coordinates

    plt.xlabel('X coordinates')
    plt.ylabel('Y coordinates')
    plt.title('Visualization of CSV Data')
    plt.grid(False)
    plt.savefig("./annotation_tool/test.PNG")
    plt.show()

# Example usage
csv_file = './csv_data/TE_C_00004.csv'
visualize_csv(csv_file)
