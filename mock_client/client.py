from typing import List, Any

from pandas import DataFrame
from prisma import Prisma, PrismaMethod
from pydantic import BaseModel


class MockClient(Prisma):
    tables: List[DataFrame]

    def __init__(self):
        super().__init__()
        self.tables = []

    # TODO: RECREATE
    def _execute(
            self,
            *,
            method: PrismaMethod,
            arguments: dict[str, Any],
            model: type[BaseModel] | None = None,
            root_selection: list[str] | None = None,
    ) -> Any:
        pass
