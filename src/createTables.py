from sqlalchemy import create_engine, text, MetaData, Column, String, Integer, Table, ForeignKey, DateTime, URL
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(os.environ['DATABASE_URL'])

# with engine.connect() as conn:
#     print(conn.execute(text("select * from accounts")).fetchall())

metadata = MetaData()

accounts = Table('accounts', metadata,
                 Column('account_id', Integer, primary_key=True),
                 Column('name', String(50)),
                 Column('address', String(50))
                 )
daily_status = Table('daily_status', metadata,
                     Column('account', Integer, ForeignKey('accounts.account_id')),
                     Column('queue', String(50), nullable=False),
                     Column('status', String(50), nullable=False),
                     Column('changed_datetime', DateTime(), nullable=False),
                     # Column('source_file', String(50), nullable=False)
                     )

monthly_status = Table('monthly_status', metadata,
                     Column('account', Integer, ForeignKey('accounts.account_id')),
                     Column('queue', String(50), nullable=False),
                     Column('status', String(50), nullable=False),
                     Column('month', Integer, nullable=False),
                     # Column('source_file', String(50), nullable=False),
                     )


metadata.create_all(engine)