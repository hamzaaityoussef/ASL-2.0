import os
import random

def trim_folders_to_50(base_path):
    # Loop through each folder in the base directory
    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        
        if os.path.isdir(folder_path):
            # List all files in the folder
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            
            # If more than 50 files, randomly delete the extras
            if len(files) > 150:
                to_delete = random.sample(files, len(files) - 50)
                
                for file_name in to_delete:
                    file_path = os.path.join(folder_path, file_name)
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
            else:
                print(f"{folder_name}: {len(files)} files, no deletion needed.")
        else:
            print(f"Skipped: {folder_path} (not a folder)")

# === Example usage ===
base_directory = 'D:/asl/ASL-2.0/DATA'  # Replace this with your actual path
trim_folders_to_50(base_directory)