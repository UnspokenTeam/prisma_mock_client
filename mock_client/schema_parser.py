import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, TypeVar, Generic, Optional, Callable, Type
from dateutil.parser import parse as parse_date

T = TypeVar("T")

prisma_types: dict[str, type] = {
    "String": str,
    "String?": Optional[str],
    "Int": int,
    "Int?": Optional[int],
    "Boolean": bool,
    "Boolean?": Optional[bool],
    "Float": float,
    "Float?": Optional[float],
    "Decimal": float,
    "Decimal?": Optional[float],
    "BigInt": int,
    "BigInt?": Optional[int],
    "DateTime": datetime,
    "DateTime?": Optional[datetime],
    "Json": dict[str, str],
    "Json?": Optional[dict[str, str]],
    "Bytes": bytes,
    "Bytes?": Optional[bytes],
}


@dataclass
class Property(Generic[T]):
    name: str
    python_type: Type[T]
    prisma_type: str
    default_value: Optional[Callable[[], Optional[T]]] = field(default=None)
    nullable: bool = field(default=True)

    @staticmethod
    def determine_type(prisma_type: str) -> type:
        cleared_type = re.search(r"\[\S+]", prisma_type)
        if cleared_type is None:
            cleared_type = prisma_type
        else:
            cleared_type = cleared_type.group()[1:-1]

        python_type = prisma_types[cleared_type]

        if cleared_type != prisma_type:
            return List[python_type]

        return python_type

    def __repr__(self) -> str:
        return f"Property(name: {self.name}, type: {self.python_type}, default: {self.default_value}, nullable: {self.nullable}, prisma_type: {self.prisma_type})"


class SchemaParser:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        data = self._read_file()
        print(data.__repr__())

    def _read_file(self) -> dict[str, List[Property]]:
        with open(self.filepath, "r") as f:
            data = f.read()
            data = self._delete_spaces(data)

        return self._generate_dict(data)

    @staticmethod
    def _generate_dict(data: str) -> dict[str, List[Property]]:
        quotes_opened = False
        word_buffer = ""
        current_object = ""
        brackets_opened = False
        skip = False
        result: dict[str, List[Property]] = {}
        i = 0
        while i < len(data):
            char = data[i]

            if char == "{" and not quotes_opened:
                word_buffer = word_buffer.strip()

                if "datasource" in word_buffer or "generator" in word_buffer:
                    skip = True
                    i += 1
                    word_buffer = ""
                    continue

                result[word_buffer.split()[1]] = []
                current_object = word_buffer.split()[1]
                word_buffer = ""
                brackets_opened = True

                i += 2
                continue

            if char == "}" and not quotes_opened:
                current_object = ""
                brackets_opened = False
                i += 1
                skip = False
                continue

            if skip:
                i += 1
                continue

            if char == "\n" and not brackets_opened:
                i += 1
                continue
            elif char == "\n":
                words = word_buffer.split()
                python_type = Property.determine_type(words[1])
                prop = Property[python_type](words[0], python_type, words[1])

                if re.search("@default\(\S+\)", word_buffer):
                    prop.default_value = SchemaParser._handle_default_value(
                        default_value=re.search(
                            "@default\(\S+\)",
                            word_buffer
                        ).group(),
                        python_type=python_type
                    )

                result[current_object].append(prop)
                word_buffer = ""
                i += 1
                continue

            if char == "\"":
                quotes_opened = not quotes_opened

            word_buffer += char

            i += 1

        return result

    @staticmethod
    def _handle_default_value(default_value: str, python_type: Type[T]) -> Callable[[], T]:
        default_value = re.search("\(\S+\)", default_value).group()
        if default_value is None:
            raise ValueError(f"Invalid default value: {default_value}")

        default_value = default_value[1:-1]
        match default_value:
            case "now()":
                return lambda: datetime.utcnow()
            case "uuid()":
                return lambda: uuid.uuid4()
            case "cuid()":
                raise NotImplementedError("CUID not yet implemented")
            case _:
                if python_type is datetime or python_type is Optional[datetime]:
                    return lambda: parse_date(default_value)
                return lambda: python_type(default_value)

    @staticmethod
    def _trim_lines(lines: List[str]) -> List[str]:
        for i in range(len(lines)):
            lines[i] = lines[i].strip()

        return lines

    @staticmethod
    def _delete_spaces(string: str) -> str:
        in_quotes = False
        i = 0
        res = ""
        while i < len(string) - 1:
            if (
                    (
                            string[i] == " " and string[i + 1] == " "
                            or string[i] == "\n" and string[i + 1] == "\n"
                            or string[i] == "\t"
                    )
                    and not in_quotes
            ):
                i += 1
                continue

            res += string[i]

            if string[i] == "\"":
                in_quotes = not in_quotes

            i += 1

        if len(string) != 0 and string[-1] != " ":
            res += string[-1]

        return res
