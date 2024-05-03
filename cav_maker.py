import os
import json
import pandas as pd
from math import sqrt

json_dir = './json_folder'
output_dir = './csv_folder'

# Desired junction types
desired_junctions = ['junc_I_open', 'junc_I_normal', 'junc_I_isolation', 'junc_I', 'junc_L', 'junc_T', 'junc_X']

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Iterate through each JSON file in the directory
for json_file in os.listdir(json_dir):
    with open(os.path.join(json_dir, json_file)) as f:
        data = json.load(f)
        
        # Extract junctions and walls from the JSON data
        junctions = {junction['id']: junction for junction in data['annotations'][0]['junctions']}
        walls = {wall['start']: wall for wall in data['annotations'][0]['walls']}
        
        # Create a list to store data for each junction
        rows = []
        for junction_id, junction in junctions.items():
            junction_type = junction['type']
            
            # Check if the junction type is in the desired junction types
            if junction_type in desired_junctions:
                position = junction['position']
                x = position['x']
                y = position['y']
                
                for connection in walls.items():
                    connected_from = connection[1]['start']
                    connected_to = connection[1]['end']
                    connection_length = connection[1]['length']
                    euclidean_distance = connection[1]['euclidean_distance']
                    if connected_from and connected_to == junction_id:
                        from_x = x
                        from_y = y
                        to_x = x
                        to_y = y
                        #print(from_x, from_y, to_x, to_y)
                        #print(connected_from, connected_to, connection_length, euclidean_distance)
                        #print(connection)

                    #print(connected_from, connected_to, connection_length, euclidean_distance)
                        #print(connection)
                        
                        rows.append([json_file, junction_type, junction_id, x, y, connected_from, connected_to, from_x, from_y, to_x, to_y, euclidean_distance])
        print(rows)
        # Create a DataFrame from the collected data
        df = pd.DataFrame(rows, columns=['json_file', 'junction_type', 'junction_id', 'x', 'y', 
                                         'connected_from', 'connected_to', 'from_x', 'from_y', 
                                        'to_x', 'to_y', 'euclidean_distance'])
        
        # Save the DataFrame to a CSV file
        output_filename = os.path.splitext(json_file)[0] + '_junctions.csv'
        output_path = os.path.join(output_dir, output_filename)
        df.to_csv(output_path, index=False)

print("CSV files created successfully.")
