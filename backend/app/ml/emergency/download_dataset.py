import kagglehub
from pathlib import Path
import shutil


print("Downloading Suicide Detection Dataset...")

download_path = kagglehub.dataset_download(
    "nikhileswarkomati/suicide-watch"
)

print(f"Downloaded dataset to: {download_path}")

source_dir = Path(download_path)
destination_dir = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "emergency"
)

destination_dir.mkdir(
    parents=True,
    exist_ok=True,
)

for file in source_dir.iterdir():
    destination = destination_dir / file.name

    if file.is_file():
        shutil.copy2(file, destination)

print(f"Dataset copied to: {destination_dir}")