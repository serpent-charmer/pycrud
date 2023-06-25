from abc import ABC
import datetime
from operator import and_
from sqlalchemy import select, insert, func, delete, update

from ..session import SessionDependency
from ..models import (
    Auction, AuctionBidLink, AuctionCancelData, 
    AuctionData, AuctionBuyoutData, AuctionPageData, 
    AuctionUser, Bid, BidData, 
    ErrorResult, OkResult
)

class AbstractService(ABC):

    def __init__(self, model):
        self.model = model


    async def crt(self):
        pass


    async def get(self, session: SessionDependency, _id: int):
        q = select(self.model).where(self.model._id == _id)
        rs = await session.execute(q)
        return rs.scalars().all()
    

    async def upd(self):
        pass


    async def dlt(self):
        pass


class AuctionService(AbstractService):
    def __init__(self):
        super().__init__(Auction)


    async def browse(self, q, sess):
        rs = await sess.execute(q)
        return rs.scalars().all()
    

    async def browse_open(self, session:SessionDependency, data:AuctionPageData):
        q = select(Auction).where(Auction.bought_by == None).limit(data.li).offset(data.off)
        return await self.browse(q, session)
    

    async def browse_closed(self, session:SessionDependency, data:AuctionPageData):
        q = select(Auction).where(Auction.bought_by != None).limit(data.li).offset(data.off)
        return await self.browse(q, session)
    

    async def crt(self, session:SessionDependency, data:AuctionData):
        n = datetime.datetime.now()
        e = n + datetime.timedelta(hours=data.hours or 8)
        q = insert(self.model).values(item_name = data.item_name, 
                                  buyout_price = data.buyout_price, 
                                    start=n, 
                                    end = e,
                                    owner_name=data.owner_name)
        await session.execute(q)
        await session.commit()


    async def upd(self, session:SessionDependency, data: AuctionBuyoutData):
        u = update(self.model) \
            .where(and_(Auction._id == data.auction_id, 
                        Auction.bought_by == None)) \
            .values(bought_by = data.buyer_name)
        await session.execute(u)
        await session.commit()
        

    async def dlt(self, session:SessionDependency, data:AuctionCancelData):
        q = delete(Auction).where(Auction._id == data.auction_id)
        await session.execute(q)
        await session.commit()

        
    async def highest_bid(self, session:SessionDependency, auction_id: int):
        model:AuctionBidLink = AuctionBidLink
        q = select(Bid) \
                    .join(model) \
                    .join(Auction).where(model.auction_id == auction_id) \
                    .order_by(Bid.amt.desc()) \
                    .limit(1)
        rs = await session.execute(q)
        return rs.scalar()
    

class AuctionUserService(AbstractService):
    def __init__(self):
        super().__init__(AuctionUser)
        

    async def get(self, session: SessionDependency, _name: str):
        q = select(self.model).where(self.model.name == _name)
        rs = await session.execute(q)
        return rs.scalars().all()
    

    async def crt(self, session: SessionDependency, name: str):
        q = insert(self.model).values(name=name)
        await session.execute(q)
        await session.commit()


class BidService(AbstractService):
    def __init__(self):
        super().__init__(Bid)


    async def crt(self, session: SessionDependency, data: BidData):
        check = select(Auction).where(and_(Auction._id == data.auction_id,
                                           and_(Auction.bought_by == None, 
                                                Auction.end > func.now())))
        crs = await session.execute(check)

        if not crs.scalars().first():
            return ErrorResult(msg="Auction is closed")
        
        q = insert(self.model)\
            .values(amt=data.amt,
                    owner_name=data.owner_name)\
            .returning(self.model._id)
        
        rs = await session.execute(q)
        bid_id = rs.scalars().first()

        if bid_id:
            q1 = insert(AuctionBidLink).values(bid_id = bid_id, auction_id = data.auction_id)
            await session.execute(q1)
            await session.commit()
            return OkResult(msg="Bid placed")
        else:
            await session.rollback()
            return ErrorResult(msg="Error placing bid")
