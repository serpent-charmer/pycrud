import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pcrud.log import log
from .service.auction_service import AuctionService, AuctionUserService, BidService
from .auction_route import AuctionRoute, AuctionUserRoute, BidRoute

app = FastAPI()

@app.exception_handler(Exception)
async def default_exception_handler(request: Request, exc: Exception):
    log.exception(exc)
    return JSONResponse(
        status_code=418,
        content={"message": "Unhandled exception, check logs"},
    )

app.include_router(AuctionRoute(AuctionService).get_router())
app.include_router(AuctionUserRoute(AuctionUserService).get_router())
app.include_router(BidRoute(BidService).get_router())
