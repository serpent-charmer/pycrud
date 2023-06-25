from datetime import datetime, timedelta
import os
import pytest
import asyncio
import pytest_asyncio
from typing import List
from sqlalchemy import func, update

from sqlalchemy.schema import CreateSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from pcrud.service.auction_service import AuctionService, AuctionUserService, BidService
from .models import Auction, AuctionBuyoutData, AuctionData, AuctionPageData, Base, Bid, BidData, ErrorResult

DB_URL = os.getenv("DB_URL") or "127.0.0.1"
DATABASE_URL = f"postgresql+asyncpg://crud_admin:password@{DB_URL}/crud_project"

test_schema = "test"
engine = create_async_engine(DATABASE_URL, echo=True, execution_options={"schema_translate_map": {None: test_schema}})
async_session = async_sessionmaker(engine, expire_on_commit=False)

@pytest_asyncio.fixture
async def sess() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_schema():
    async with engine.begin() as conn:
        check = await conn.run_sync(engine.dialect.has_schema, test_schema)
        if not check:
            await conn.execute(CreateSchema(test_schema))


@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
a = AuctionService()
au = AuctionUserService()
b = BidService()

@pytest.mark.asyncio
async def test_auction_add(sess: AsyncSession):
    p = AuctionPageData(li=1, off=0)
    owner_name = "test"
    item_name = "hello"
    await au.crt(sess, owner_name)
    await a.crt(sess, AuctionData(buyout_price=50, item_name=item_name, owner_name=owner_name, hours=8))

    rs:List[Auction] = await a.browse_open(sess, p)
    auc = rs[0]

    assert "hello" == auc.item_name and auc.bought_by == None

@pytest.mark.asyncio
async def test_auction_bid(sess: AsyncSession):
    owner_name = "test2"
    item_name = "hello"
    await au.crt(sess, owner_name)
    await a.crt(sess, AuctionData(buyout_price=50, item_name=item_name, owner_name=owner_name, hours=8))

    bidder1 = "b1"
    bidder2 = "b2"
    bidder3 = "b3"

    await au.crt(sess, bidder1)
    await au.crt(sess, bidder2)
    await au.crt(sess, bidder3)

    h = 29.323
    last = BidData(owner_name=bidder3, amt=h, auction_id=1)
    print(last.amt, type(h))

    await b.crt(sess, BidData(owner_name=bidder1, amt=8.323, auction_id=1))
    await b.crt(sess, BidData(owner_name=bidder2, amt=1.323, auction_id=1))
    await b.crt(sess, last)

    rs:Bid = await a.highest_bid(sess, 1)

    assert rs != None and rs.amt == h


@pytest.mark.asyncio
async def test_auction_bid_closed(sess: AsyncSession):
    owner_name = "test1"
    item_name = "hello"
    await au.crt(sess, owner_name)
    await a.crt(sess, AuctionData(buyout_price=50, item_name=item_name, owner_name=owner_name, hours=8))
    await a.upd(sess, AuctionBuyoutData(auction_id=1, buyer_name=owner_name))

    bid_info:ErrorResult = await b.crt(sess, BidData(owner_name=owner_name, amt=8.323, auction_id=1))

    assert bid_info != None and bid_info.msg == "Auction is closed"

@pytest.mark.asyncio
async def test_auction_bid_expired(sess: AsyncSession):
    owner_name = "test1"
    item_name = "hello"


    await au.crt(sess, owner_name)
    await a.crt(sess, AuctionData(buyout_price=50, item_name=item_name, owner_name=owner_name, hours=8))

    q = update(Auction).where(Auction._id == 1).values(end = datetime(1970, 12, 1))
    await sess.execute(q)

    bid_info:ErrorResult = await b.crt(sess, BidData(owner_name=owner_name, amt=8.323, auction_id=1))

    assert bid_info != None and bid_info.msg == "Auction is closed"

@pytest.mark.asyncio
async def test_auction_closed(sess: AsyncSession):
    owner_name = "test1"
    item_name = "hello"
    await au.crt(sess, owner_name)
    await a.crt(sess, AuctionData(buyout_price=50, item_name=item_name, owner_name=owner_name, hours=8))
    await a.upd(sess, AuctionBuyoutData(auction_id=1, buyer_name=owner_name))
    closed:List[Auction] = await a.browse_closed(sess, AuctionPageData(li=1, off=0))

    assert closed[0].bought_by == owner_name