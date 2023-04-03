
from sqlalchemy.orm import Session
from models import engine, db_listing_entry, Base

Base.metadata.create_all(bind=engine)

with Session(engine) as session:
    listings = session.query(db_listing_entry).all()
    for listing in listings:
        print(listing)

