
import sys
from pathlib import Path
from pydantic import BaseModel
import kubiya

action_store = kubiya.ActionStore("sample-store", "0")

@action_store.kubiya_action(validate_input=True)
def simple_action(a: str):
    "returns bar"
    return f"hi {a} from simple_action"


class ExampleModel(BaseModel):
    """used for type hints, automatic decumentation and validation"""
    your_string: str
    your_int: int

@action_store.kubiya_action(validate_input=True)
def action_with_model(user: ExampleModel) -> str:
    """returns baz"""
    return f"{user.get('your_string')} | {user.get('your_int')} | {user.get('email')} from baz"

