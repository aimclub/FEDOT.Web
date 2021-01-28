from dataclasses import dataclass


@dataclass
class Model:
    model_id: str = '0'
    label: str = 'model_label'
    description: str = 'model description'
