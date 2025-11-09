# reflect_table.py
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

metadata = MetaData()
metadata.reflect(bind=engine)

table_name = "bad_logs" 
if table_name not in metadata.tables:
    raise ValueError(f"Table '{table_name}' not found in database.")

bad_logs_table = metadata.tables[table_name]

# Print schema
print("\n📋 Table columns:")
for col in bad_logs_table.columns:
    print(f"{col.name} ({col.type}) nullable={col.nullable} default={col.default}")
# Query
with Session(engine) as session:
    result = session.execute(bad_logs_table.select().limit(5))
    for row in result:
        print(row)
