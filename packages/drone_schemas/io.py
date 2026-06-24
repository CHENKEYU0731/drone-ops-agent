from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel


ModelT = TypeVar("ModelT", bound=BaseModel)


def read_json_file(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"输入文件不存在: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 文件格式无效: {path}: {exc}") from exc


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def write_model(path: Path, model: BaseModel) -> None:
    write_json(path, model.model_dump(mode="json"))


def write_model_list(path: Path, models: list[BaseModel]) -> None:
    write_json(path, [model.model_dump(mode="json") for model in models])


def load_model(path: Path, model_type: type[ModelT]) -> ModelT:
    return model_type.model_validate(read_json_file(path))


def load_model_list(path: Path, model_type: type[ModelT]) -> list[ModelT]:
    data = read_json_file(path)
    if not isinstance(data, list):
        raise ValueError(f"JSON 文件必须是列表: {path}")
    return [model_type.model_validate(item) for item in data]
