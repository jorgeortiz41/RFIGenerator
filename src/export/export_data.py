from pathlib import Path
import shutil


def save_file(input_file, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_file, output_path)
    return output_path


def save_data(data, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if isinstance(data, str):
        with open(output_path, 'w') as f:
            f.write(data)
    elif hasattr(data, 'to_csv'):
        data.to_csv(output_path, index=False)
    else:
        import json
        with open(output_path, 'w') as f:
            json.dump(data, f)
    
    return output_path
