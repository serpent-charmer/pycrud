from functools import partial
import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import mapped_column, DeclarativeBase


class ServiceResult(BaseModel):
    msg:str

class OkResult(ServiceResult):
    pass

class ErrorResult(ServiceResult):
    pass

class AuctionPageData(BaseModel):
    li:int
    off:int

class AuctionBuyoutData(BaseModel):
    auction_id:int
    buyer_name:str

class AuctionData(BaseModel):
    buyout_price:float
    item_name:str
    owner_name:str
    hours:int

class AuctionCancelData(BaseModel):
    auction_id:int

class AuctionUserData(BaseModel):
    user_name:str

class BidData(BaseModel):
    owner_name: str
    amt: float
    auction_id: int


class Base(DeclarativeBase):
    pass

def wrap_column(*args, **kwargs):
    return mapped_column(*args, nullable=False, **kwargs)

class AuctionUser(Base):
    __tablename__ = 'auction_user'
    name = mapped_column(sa.String(50), primary_key=True)


class Bid(Base):
    __tablename__ = 'bid'
    _id = mapped_column(sa.Integer, primary_key=True)
    amt = wrap_column(sa.Double)
    owner_name = wrap_column(sa.String(50), sa.ForeignKey('auction_user.name'))

class Auction(Base):
    __tablename__ = 'auction'
    _id = mapped_column(sa.Integer, primary_key=True)
    item_name = wrap_column(sa.String(50))
    buyout_price = wrap_column(sa.Double)
    start = mapped_column(sa.DateTime)
    end = mapped_column(sa.DateTime)
    owner_name = wrap_column(sa.String(50), sa.ForeignKey('auction_user.name'))
    bought_by = mapped_column(sa.String(50), sa.ForeignKey('auction_user.name'))
    

class AuctionBidLink(Base):
    __tablename__ = 'auction_bid_link'
    _id = mapped_column(sa.Integer, primary_key=True)
    bid_id = mapped_column(sa.Integer, sa.ForeignKey('bid._id', ondelete="CASCADE"))
    auction_id = mapped_column(sa.Integer, sa.ForeignKey('auction._id', ondelete="CASCADE"))
