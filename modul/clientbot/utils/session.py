from typing import Optional

from aiohttp import ClientSession


class Client:
    def __init__(self):
        self._session: Optional[ClientSession] = None

    @property
    def session(self):
        if self._session is None or self._session.closed:
            self._session = ClientSession()
        return self._session

    async def close(self):
        if self._session is not None:
            if not self._session.closed:
                await self._session.close()
