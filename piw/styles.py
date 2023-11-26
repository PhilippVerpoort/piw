from pathlib import Path

import yaml


BASE_PATH = Path(__file__).parent.resolve()


with open(BASE_PATH / 'config' / 'styles.yml', 'r') as file_handle:
    default_styles = yaml.load(file_handle.read(), Loader=yaml.FullLoader)
