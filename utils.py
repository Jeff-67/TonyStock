# type: ignore
# flake8: noqa

import base64
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import pymongo
import redis
from mysql.connector import Error as MySQLError
from mysql.connector import connect
from pymongo import MongoClient
from pymongo import errors as MongoErrors

from settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages connections and operations for Redis, MongoDB, and MySQL databases.
    """

    def __init__(self):
        self.settings = Settings()
        self.redis_client = self._init_redis()
        self.mongo_client, self.mongo_db = self._init_mongo()
        self.mysql_config = self.settings.mysql_config

    # ------------------- Redis Operations -------------------

    def _init_redis(self) -> Optional[redis.Redis]:
        try:
            pool = redis.ConnectionPool(
                host=self.settings.redis_config["host"],
                port=self.settings.redis_config["port"],
                db=self.settings.redis_config["db"],
                password=self.settings.redis_config.get("password"),
                max_connections=self.settings.redis_config["max_connections"],
                decode_responses=True,
            )
            client = redis.Redis(connection_pool=pool)
            client.ping()
            logger.info("Connected to Redis.")
            return client
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return None

    def _cache_data(self, key: str, data: Any, expiration: int = 3600) -> bool:
        if not self.redis_client:
            logger.error("Redis client unavailable.")
            return False
        try:
            serialized = self.serialize(data)
            if not serialized:
                logger.error("Serialization failed. Data not cached.")
                return False
            self.redis_client.set(key, serialized, ex=expiration)
            logger.info(f"Data cached in Redis with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Caching error: {e}")
            return False

    def _get_cached_data(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            logger.error("Redis client unavailable.")
            return None
        try:
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache hit for key: {key}")
                return self.deserialize(cached)
            logger.info(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return None

    # ------------------- MongoDB Operations -------------------

    def _init_mongo(self) -> Tuple[Optional[MongoClient], Optional[Any]]:
        try:
            client = MongoClient(
                self.settings.mongo_config["uri"],
                username=self.settings.mongo_config.get("username"),
                password=self.settings.mongo_config.get("password"),
                maxPoolSize=self.settings.mongo_config["max_pool_size"],
            )
            client.admin.command("ping")
            logger.info("Connected to MongoDB.")
            db = client[self.settings.mongo_config["db_name"]]
            return client, db
        except MongoErrors.ConnectionFailure as e:
            logger.error(f"MongoDB connection error: {e}")
            return None, None

    def _insert_into_mongo(
        self, data: Union[Dict, List[Dict]], key: str, collection: str
    ) -> bool:
        if self.mongo_db is None:
            logger.error("MongoDB database unavailable.")
            return False
        try:
            coll = self.mongo_db[collection]
            result = (
                coll.insert_many(data)
                if isinstance(data, list)
                else coll.insert_one(data)
            )
            count = (
                len(result.inserted_ids)
                if isinstance(result, pymongo.results.InsertManyResult)
                else 1
            )
            logger.info(f"Inserted {count} document(s) into '{collection}'.")
            for record in data if isinstance(data, list) else [data]:
                cache_key = self._generate_cache_key(collection, key, record.get(key))
                self._cache_data(cache_key, record)
            return True
        except MongoErrors.PyMongoError as e:
            logger.error(f"MongoDB insertion error: {e}")
            return False

    def _fetch_from_mongo(
        self, query: Dict, key: str, collection: str
    ) -> Optional[List[Dict]]:
        if self.mongo_db is None:
            logger.error("MongoDB database unavailable.")
            return None
        try:
            coll = self.mongo_db[collection]
            logger.info(f"Fetching from MongoDB: {query}")
            documents = list(coll.find(query))
            if documents:
                for doc in documents:
                    doc["_id"] = str(doc["_id"])
                cache_key = self._generate_cache_key(collection, key, query.get(key))
                self._cache_data(cache_key, documents)
                logger.info(
                    f"Fetched and cached {len(documents)} document(s) from '{collection}'."
                )
                return documents
            logger.info(f"No documents found in '{collection}' for query.")
            return None
        except MongoErrors.PyMongoError as e:
            logger.error(f"MongoDB fetch error: {e}")
            return None

    # ------------------- MySQL Operations -------------------

    def _init_mysql_connection(self) -> Optional[Any]:
        try:
            conn = connect(
                host=self.mysql_config["host"],
                port=self.mysql_config.get("port", 3305),
                user=self.mysql_config["username"],
                password=self.mysql_config["password"],
                database=self.mysql_config["database"],
            )
            if conn.is_connected():
                logger.info("Connected to MySQL.")
                return conn
        except MySQLError as e:
            logger.error(f"MySQL connection error: {e}")
            return None

    def _insert_into_mysql(
        self, table: str, key: str, data: Union[Dict, List[Dict]]
    ) -> bool:
        conn = self._init_mysql_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                if isinstance(data, dict):
                    self._execute_mysql_insert(cursor, table, data)
                    cache_key = self._generate_cache_key(table, key, data.get(key))
                    self._cache_data(cache_key, data)
                elif isinstance(data, list):
                    for record in data:
                        self._execute_mysql_insert(cursor, table, record)
                        cache_key = self._generate_cache_key(
                            table, key, record.get(key)
                        )
                        self._cache_data(cache_key, record)
                else:
                    logger.error("Invalid data type for MySQL insertion.")
                    return False
            conn.commit()
            logger.info(f"Inserted data into MySQL table '{table}'.")
            return True
        except MySQLError as e:
            logger.error(f"MySQL insertion error: {e}")
            return False
        finally:
            conn.close()
            logger.info("MySQL connection closed.")

    def _execute_mysql_insert(self, cursor, table: str, data: Dict):
        columns = ", ".join(f"`{k}`" for k in data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
        values = tuple(data.values())
        cursor.execute(sql, values)

    def _fetch_from_mysql(
        self, query: str, key: str, table: Optional[str] = None
    ) -> Optional[List[Dict]]:
        conn = self._init_mysql_connection()
        if not conn:
            return None
        try:
            with conn.cursor(dictionary=True) as cursor:
                logger.info(f"Executing MySQL query: {query}")
                cursor.execute(query)
                results = cursor.fetchall()
                if results:
                    cache_key = self._generate_cache_key(table or "mysql", key, query)
                    self._cache_data(cache_key, results)
                    logger.info(
                        f"Fetched and cached {len(results)} record(s) from MySQL."
                    )
                    return results
                logger.info("No records found for the query.")
                return None
        except MySQLError as e:
            logger.error(f"MySQL fetch error: {e}")
            return None
        finally:
            conn.close()
            logger.info("MySQL connection closed.")

    # ------------------- General Operations -------------------

    def get_data(
        self,
        db_type: str,
        key: str,
        query: Union[Dict, str],
        collection_or_table: Optional[str] = None,
    ) -> Optional[Any]:
        cache_key = self._generate_cache_key(
            collection_or_table,
            key,
            query.get(key) if isinstance(query, dict) else None,
        )
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        if not collection_or_table:
            logger.error("Collection or table name is required.")
            return None

        if db_type.lower() == "mongo":
            if not isinstance(query, dict):
                logger.error("MongoDB query must be a dictionary.")
                return None
            return self._fetch_from_mongo(query, key, collection_or_table)
        elif db_type.lower() == "mysql":
            if not isinstance(query, str):
                logger.error("MySQL query must be a string.")
                return None
            return self._fetch_from_mysql(query, key, collection_or_table)
        else:
            logger.error(f"Unsupported database type: {db_type}")
            return None

    def insert_data(
        self,
        db_type: str,
        data: Union[Dict, List[Dict]],
        key: Optional[str] = None,
        table: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> bool:
        db_type = db_type.lower()
        if db_type == "mongo":
            if not key or not collection:
                logger.error("MongoDB requires both key and collection name.")
                return False
            return self._insert_into_mongo(data, key, collection)
        elif db_type == "mysql":
            if not table or not key:
                logger.error("MySQL requires both table name and key.")
                return False
            return self._insert_into_mysql(table, key, data)
        else:
            logger.error(f"Unsupported database type: {db_type}")
            return False

    # ------------------- Helper Methods -------------------

    def _generate_cache_key(
        self, collection_or_table: str, key: str, value: Optional[str]
    ) -> str:
        encoded = (
            base64.urlsafe_b64encode(str(value).encode()).decode() if value else ""
        )
        return f"{collection_or_table}:{key}:{encoded}"

    @staticmethod
    def serialize(data: Any) -> str:
        try:
            return json.dumps(data, default=str)
        except TypeError as e:
            logger.error(f"Serialization error: {e}")
            return ""

    @staticmethod
    def deserialize(data_str: str) -> Optional[Any]:
        try:
            return json.loads(data_str)
        except json.JSONDecodeError as e:
            logger.error(f"Deserialization error: {e}")
            return None


def main():
    db_manager = DatabaseManager()

    # ------------------- Insert Documents into MongoDB -------------------
    mongo_documents = [
        {
            "url": "https://www.example.com/article1",
            "title": "Article 1 Title",
            "content": "Content of the first article.",
            "author": "Author A",
        },
        {
            "url": "https://www.example.com/article2",
            "title": "Article 2 Title",
            "content": "Content of the second article.",
            "author": "Author B",
        },
        {
            "url": "https://www.example.com/article3",
            "title": "Article 3 Title",
            "content": "Content of the third article.",
            "author": "Author C",
        },
    ]

    if db_manager.insert_data(
        db_type="mongo", data=mongo_documents, collection="articles", key="url"
    ):
        logger.info("Inserted multiple documents into MongoDB.")
    else:
        logger.error("Failed to insert documents into MongoDB.")

    # ------------------- Insert Single Document into MongoDB -------------------
    mongo_document = {
        "url": "https://www.example.com/article4",
        "title": "Article 4 Title",
        "content": "Content of the fourth article.",
        "author": "Author D",
    }

    if db_manager.insert_data(
        db_type="mongo", data=mongo_document, collection="articles", key="url"
    ):
        logger.info("Inserted single document into MongoDB.")
    else:
        logger.error("Failed to insert single document into MongoDB.")

    # ------------------- Insert Record into MySQL -------------------
    mysql_record = {
        "ticker": "2330",
        "company_name": "台積電",
    }

    if db_manager.insert_data(
        db_type="mysql", data=mysql_record, table="TWSE", key="ticker"
    ):
        logger.info("Inserted record into MySQL.")
    else:
        logger.error("Failed to insert record into MySQL.")

    # ------------------- Insert List of Records into MySQL -------------------
    mysql_records = [
        {"ticker": "8299", "company_name": "群聯"},
        {"ticker": "3036", "company_name": "文曄"},
        {"ticker": "3413", "company_name": "京鼎"},
        {"ticker": "7715", "company_name": "裕山"},
    ]

    if db_manager.insert_data(
        db_type="mysql", data=mysql_records, table="TWSE", key="ticker"
    ):
        logger.info("Inserted list of records into MySQL.")
    else:
        logger.error("Failed to insert list of records into MySQL.")

    # ------------------- Fetch and Cache Verification -------------------

    # Fetch MongoDB Documents
    mongo_queries = [
        {"url": "https://www.example.com/article1"},
        {"url": "https://www.example.com/article2"},
        {"url": "https://www.example.com/article3"},
    ]

    for query in mongo_queries:
        data = db_manager.get_data(
            db_type="mongo", key="url", query=query, collection_or_table="articles"
        )
        if data:
            logger.info(f"Retrieved MongoDB data for {query['url']}: {data}")
        else:
            logger.error(f"Failed to retrieve MongoDB data for {query['url']}.")

    # Fetch MySQL Record
    mysql_query = "SELECT * FROM TWSE WHERE ticker = '2330'"

    mysql_data = db_manager.get_data(
        db_type="mysql", key="ticker", query=mysql_query, collection_or_table="TWSE"
    )
    if mysql_data:
        logger.info(
            f"Retrieved MySQL data for ticker {mysql_record['ticker']}: {mysql_data}"
        )
    else:
        logger.error(
            f"Failed to retrieve MySQL data for ticker {mysql_record['ticker']}."
        )

    # ------------------- Direct Cache Retrieval -------------------

    # Retrieve Cached MongoDB Data
    for query in mongo_queries:
        cache_key = db_manager._generate_cache_key("articles", "url", query["url"])
        cached_data = db_manager._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Cached MongoDB data for {query['url']}: {cached_data}")
        else:
            logger.error(f"No cached data found for {query['url']}.")

    # Retrieve Cached MySQL Data
    cache_key = db_manager._generate_cache_key("TWSE", "ticker", mysql_record["ticker"])
    cached_mysql = db_manager._get_cached_data(cache_key)
    if cached_mysql:
        logger.info(
            f"Cached MySQL data for ticker {mysql_record['ticker']}: {cached_mysql}"
        )
    else:
        logger.error(f"No cached data found for ticker {mysql_record['ticker']}.")


if __name__ == "__main__":
    main()
