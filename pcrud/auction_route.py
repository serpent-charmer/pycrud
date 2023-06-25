from abc import ABC
from functools import wraps

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pcrud.log import log

from pcrud.models import (
    AuctionCancelData, AuctionData,
    AuctionBuyoutData, AuctionPageData,
    AuctionUserData, BidData, ErrorResult, OkResult
)

from .service.auction_service import AbstractService, AuctionService
from .session import SessionDependency


def wrap_response(sub):

    @wraps(sub)
    async def w(*args, **kwargs):
        try:
            rs = await sub(*args, **kwargs)
            match rs:
                case None:
                    return JSONResponse({"message": "ok"})
                case OkResult(msg=m):
                    return JSONResponse({"message": m})
                case ErrorResult(msg=m):
                    return JSONResponse(status_code=400, content={"message": m})
                case _ as o:
                    return o
        except Exception as e:
            log.exception(e)
            return JSONResponse(status_code=400, content={"message": type(e).__name__})
    return w


class AbstractRoute(ABC):

    def __init__(self, route_name, service_class: AbstractService):

        self.router = APIRouter(
            prefix=f"/{route_name}",
            tags=[f"{route_name}"]
        )
        self.service: AbstractService = service_class()

    def get_router(self):
        return self.router


class AuctionRoute(AbstractRoute):

    service: AuctionService

    def __init__(self, service_class):
        super().__init__("auction", service_class)

        @self.router.get("/open")
        @wrap_response
        async def _get(myses: SessionDependency, data: AuctionPageData):
            return await self.service.browse_open(myses, data)

        @self.router.get("/closed")
        @wrap_response
        async def _get(myses: SessionDependency, data: AuctionPageData):
            return await self.service.browse_closed(myses, data)

        @self.router.post("/crt")
        @wrap_response
        async def _post(myses: SessionDependency, data: AuctionData):
            return await self.service.crt(myses, data)

        @self.router.get("/highest_bid/{auction_id}")
        @wrap_response
        async def _get(myses: SessionDependency, auction_id: int):
            return await self.service.highest_bid(myses, auction_id)

        @self.router.patch("/upd")
        @wrap_response
        async def _patch(myses: SessionDependency, data: AuctionBuyoutData):
            return await self.service.upd(myses, data)

        @self.router.delete("/dlt")
        @wrap_response
        async def _delete(myses: SessionDependency, data: AuctionCancelData):
            return await self.service.dlt(myses, data)


class AuctionUserRoute(AbstractRoute):

    def __init__(self, service_class: AbstractService):
        super().__init__("auction_user", service_class)

        @self.router.get("/get")
        @wrap_response
        async def _get(myses: SessionDependency, usr_data: AuctionUserData):
            return await self.service.get(myses, usr_data.user_name)

        @self.router.post("/crt")
        @wrap_response
        async def _post(myses: SessionDependency, usr_data: AuctionUserData):
            return await self.service.crt(myses, usr_data.user_name)


class BidRoute(AbstractRoute):

    def __init__(self, service_class: AbstractService):
        super().__init__("bid", service_class)

        @self.router.get("/get/{bid_id}")
        @wrap_response
        async def _get(myses: SessionDependency, bid_id: int):
            return await self.service.get(myses, bid_id)

        @self.router.post("/crt")
        @wrap_response
        async def _post(myses: SessionDependency, data: BidData):
            return await self.service.crt(myses, data)
