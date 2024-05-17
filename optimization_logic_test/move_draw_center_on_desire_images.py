import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import xml.etree.ElementTree as ET

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_xml(xml_file, valid_junction_types, other_objects):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    junctions = []
    mask_areas = []

    for obj in root.iter('object'):
        label = obj.find('name').text
        bndbox = obj.find('bndbox')
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)
        if label in valid_junction_types:
            junctions.append((label, xmin, ymin, xmax, ymax))
        if label in other_objects:
            mask_areas.append((xmin, ymin, xmax, ymax))
    return junctions, mask_areas

def mask_objects(dilated, mask_areas):
    for xmin, ymin, xmax, ymax in mask_areas:
        cv2.rectangle(dilated, (xmin, ymin), (xmax, ymax), (0, 0, 0), -1)

def is_straight_line(pts):
    if len(pts) < 2:
        return False
    pts = np.array(pts)
    dists = np.sqrt(np.sum(np.diff(pts, axis=0)**2, axis=1))
    total_dist = np.sum(dists)
    direct_dist = np.sqrt(np.sum((pts[0] - pts[-1])**2))
    return np.isclose(total_dist, direct_dist, rtol=0.01)

def find_intersections(dilated, bbox):
    xmin, ymin, xmax, ymax = bbox
    points = {
        'top': [(x, ymin) for x in range(xmin, xmax + 1) if dilated[ymin, x] > 0],
        'bottom': [(x, ymax) for x in range(xmin, xmax + 1) if dilated[ymax, x] > 0],
        'left': [(xmin, y) for y in range(ymin, ymax + 1) if dilated[y, xmin] > 0],
        'right': [(xmax, y) for y in range(ymin, ymax + 1) if dilated[y, xmax] > 0]
    }
    
    filtered_intersections = {}
    for side, pts in points.items():
        if is_straight_line(pts):
            if len(pts) >= 2:
                center = {
                    'top': ((xmin + xmax) // 2, ymin),
                    'bottom': ((xmin + xmax) // 2, ymax),
                    'left': (xmin, (ymin + ymax) // 2),
                    'right': (xmax, (ymin + ymax) // 2)
                }[side]
                pts.sort(key=lambda p: (p[0] - center[0]) ** 2 + (p[1] - center[1]) ** 2)
                filtered_intersections[side] = pts[:2]
            elif len(pts) == 1:
                filtered_intersections[side] = pts
    
    return filtered_intersections

def find_parallel_lines(bbox, intersections):
    xmin, ymin, xmax, ymax = bbox
    parallel_lines = []
    for side, pts in intersections.items():
        if len(pts) == 2:
            pt1, pt2 = pts
            if side in ['top', 'bottom']:
                parallel_lines.append(((xmin, pt1[1]), (xmax, pt2[1])))
            else:
                parallel_lines.append(((pt1[0], ymin), (pt2[0], ymax)))
    return parallel_lines

def is_point_on_parallel_line(pt, parallel_lines):
    for line in parallel_lines:
        (x1, y1), (x2, y2) = line
        if x1 == x2:  # Vertical line
            if pt[0] == x1 and y1 <= pt[1] <= y2:
                return True
        elif y1 == y2:  # Horizontal line
            if pt[1] == y1 and x1 <= pt[0] <= x2:
                return True
    return False

def draw_bounding_boxes_and_centers(image_path, junctions, mask_areas, junction_types):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, otsu_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    edges = cv2.Canny(otsu_thresh, 50, 150, apertureSize=3)
    dilated = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)

    mask_objects(dilated, mask_areas)

    img_with_boxes = cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)
    img_with_mask = img.copy()

    for idx, (label, xmin, ymin, xmax, ymax) in enumerate(junctions):
        intersections = find_intersections(dilated, (xmin, ymin, xmax, ymax))
        parallel_lines = find_parallel_lines((xmin, ymin, xmax, ymax), intersections)
        cv2.rectangle(img_with_boxes, (xmin, ymin), (xmax, ymax), (0, 255, 0), 1)
        cv2.putText(img_with_boxes, f"{idx}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        center_x = (xmin + xmax) // 2
        center_y = (ymin + ymax) // 2
        cv2.circle(img_with_boxes, (center_x, center_y), 3, (255, 0, 0), -1)
        cv2.circle(img_with_mask, (center_x, center_y), 3, (255, 0, 0), -1)

        midpoints = []
        for side, points in intersections.items():
            if len(points) == 2:
                pt1, pt2 = points
                midpoint = ((pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2)
                if is_point_on_parallel_line(midpoint, parallel_lines):
                    midpoints.append(midpoint)
                    cv2.circle(img_with_boxes, pt1, 3, (255, 255, 0), -1)
                    cv2.circle(img_with_boxes, pt2, 3, (255, 255, 0), -1)
                    cv2.circle(img_with_boxes, midpoint, 3, (0, 0, 255), -1)
                    cv2.circle(img_with_mask, midpoint, 3, (0, 0, 255), -1)
            elif len(points) == 1:
                pt1 = points[0]
                if is_point_on_parallel_line(pt1, parallel_lines):
                    midpoints.append(pt1)
                    cv2.circle(img_with_boxes, pt1, 3, (255, 255, 0), -1)
                    cv2.circle(img_with_mask, pt1, 3, (255, 255, 0), -1)

        # Check the number of midpoints for the junction type and remove excess midpoints
        expected_midpoints = junction_types.get(label, 0)
        if len(midpoints) != expected_midpoints:
            print(f"Warning: Junction {label} at index {idx} has {len(midpoints)} midpoints, expected {expected_midpoints}")
            if len(midpoints) > expected_midpoints:
                # Sort midpoints by their distance to the center of the bbox and keep the closest ones
                midpoints = sorted(midpoints, key=lambda pt: (pt[0] - center_x) ** 2 + (pt[1] - center_y) ** 2)
                midpoints = midpoints[:expected_midpoints]
        
        # Redraw the final filtered midpoints on the images
        for midpoint in midpoints:
            cv2.circle(img_with_boxes, midpoint, 3, (0, 0, 255), -1)
            cv2.circle(img_with_mask, midpoint, 3, (0, 0, 255), -1)

    return img_with_boxes, img_with_mask

xml_dir = './images/VA_D_00012.xml'
image_path = './images/VA_D_00012.PNG'
output_folder_path = './output_images'
ensure_dir(output_folder_path)

valid_junction_types = ["junc_I", "junc_I_normal", "junc_I_open", "junc_I_isolation", "junc_L", "junc_T", "junc_X"]
other_objects = ["door_normal", "door_double", "window", "door_hinged"]
junction_types = {
    "junc_I": 1,
    "junc_I_normal": 1,
    "junc_I_open": 1,
    "junc_I_isolation": 1,
    "junc_L": 2,
    "junc_T": 3,
    "junc_X": 4
}

junctions, mask_areas = parse_xml(xml_dir, valid_junction_types, other_objects)
final_image, masked_image = draw_bounding_boxes_and_centers(image_path, junctions, mask_areas, junction_types)

output_image_path = os.path.join(output_folder_path, 'final_image_with_junctions_and_centers.png')
cv2.imwrite(output_image_path, final_image)

masked_image_path = os.path.join(output_folder_path, 'masked_image.png')
cv2.imwrite(masked_image_path, masked_image)

plt.figure(figsize=(45, 25))

plt.subplot(1, 3, 1)
plt.imshow(cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB))
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 3, 2)
plt.imshow(cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB))
plt.title('Final Image with Junctions, Centers, and Valid Intersections')
plt.axis('off')

plt.subplot(1, 3, 3)
plt.imshow(cv2.cvtColor(masked_image, cv2.COLOR_BGR2RGB))
plt.title('Masked Image with Centers and Midpoints')
plt.axis('off')

plt.savefig('./111.png')
plt.show()
