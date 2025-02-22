import os
from converter import convert_file

def main():
    print("Welcome to the CAD File Converter!")
    mode = input("Do you want to convert a single file or a folder? (Enter 'file' or 'folder'): ").strip().lower()
    
    cad_files = []
    if mode == "folder":
        input_folder = input("Enter the path to the folder containing CAD files: ").strip()
        for f in os.listdir(input_folder):
            if f.lower().endswith(('.iges', '.igs', '.step', '.stp', '.brep')):
                cad_files.append(os.path.join(input_folder, f))
        if not cad_files:
            print("No supported CAD files found in that folder.")
            return
        print(f"Found {len(cad_files)} CAD file(s) in the folder.")
    elif mode == "file":
        input_file = input("Enter the path to your input CAD file (STEP, IGES, BRep): ").strip()
        if not os.path.isfile(input_file):
            print("The specified file does not exist...")
            return
        cad_files.append(input_file)
    else:
        print("Invalid mode selected. Please run the tool again and choose 'file' or 'folder'.")
        return

    output_dir = input("Enter the path to the output folder: ").strip()
    
    while True:
        output_format = input("Enter the desired output format (step, iges, brep, stl): ").strip().lower()
        if output_format in ["step", "iges", "brep", "stl"]:
            break
        print("Invalid format. Please enter 'step', 'iges', 'brep', or 'stl'.")

    stl_deflection = None
    if output_format == "stl":
        while True:
            deflection_input = input("Enter the maximum allowed deviation between the original geometry and the created STL mesh (e.g., 0.1): ").strip()
            try:
                stl_deflection = float(deflection_input)
                break
            except Exception as e:
                print("Invalid input, please enter a valid number.")
    
    # Ask about sewing/joining only if at least one file is IGES.
    sew = False
    if any(f.lower().endswith(('.iges', '.igs')) for f in cad_files):
        answer = input("When converting from IGES files, would you like to attempt to join surfaces into a solid? (y/n): ").strip().lower()
        if answer.startswith('y'):
            sew = True

    successes = 0
    skips = 0
    failures = 0

    print("\nStarting batch conversion...\n")
    for file in cad_files:
        print(f"Processing file: {file}")
        try:
            result = convert_file(file, output_format, output_dir, sew, batch_mode=(mode == "folder"), stl_deflection=stl_deflection)
            if isinstance(result, tuple):
                status, message_or_file = result
                if status == "skipped":
                    print(f"  ❗ Skipped conversion (same type): {message_or_file}\n")
                    skips += 1
                elif status == "message":
                    print(f"  ❗ {message_or_file}\n")
                    skips += 1
                elif status == "success":
                    print(f"  🎉 Converted to: {message_or_file}\n")
                    successes += 1
            else:
                print(f"  🎉 Converted to: {result}\n")
                successes += 1
        except Exception as e:
            print(f"  😔 Failed to convert {file}: {e}\n")
            failures += 1

    print("Batch conversions completed." if mode == "folder" else "Conversion completed.")
    print(f"Total files processed: {len(cad_files)}")
    print(f"Successful conversions: {successes}")
    print(f"Skipped conversions: {skips}")
    print(f"Failed conversions: {failures}")

if __name__ == "__main__":
    main()
