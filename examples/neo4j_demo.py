"""Run against your own synthetic Product graph, using a read-only account."""

import os

from neo4j import GraphDatabase

from enterprise_graphrag.adapters.neo4j import Neo4jReadClient, ReadOnlyNeo4jAdapter

schema = "Product(name: STRING, stock: INTEGER, price: FLOAT)"
with GraphDatabase.driver(
    os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
) as driver:
    client = Neo4jReadClient(driver, schema, database=os.getenv("NEO4J_DATABASE", "neo4j"))
    adapter = ReadOnlyNeo4jAdapter(client)
    rows = adapter.run("MATCH (p:Product) WHERE p.stock < $threshold RETURN p.name, p.stock", {"threshold": 10})
    print(rows)
