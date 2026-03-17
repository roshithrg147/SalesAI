# ==========================================
# Developer: Mr. R.
# Project:   HypeMind
# ==========================================

import json
import boto3
from cachetools import cached, TTLCache
from config import Config, setup_logger

logger = setup_logger("db.database")

@cached(cache=TTLCache(maxsize=10, ttl=600))
def get_product_context(filter_category=None):
    """
    Loads the product list from AWS DynamoDB.
    Leverages a 10-minute in-memory TTLCache to eliminate full-table scans.
    Optionally filters by category to save LLM context window tokens.
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(Config.PRODUCTS_TABLE)
        
        # In a real heavy-use scenario we would use a Query with secondary indexes, 
        # but for a small catalog Scan is sufficient and matches the requested logic.
        response = table.scan()
        items = response.get('Items', [])
        
        context = "Available Products:\n"
        for item in items:
            # DynamoDB scan returns flat items, we assume item has a 'category' key
            category = item.get('category', 'Uncategorized')
            if filter_category and category != filter_category:
                continue
                
            sizes_list = item.get('sizes', [])
            sizes_str = ', '.join(sizes_list) if isinstance(sizes_list, list) else sizes_list
                
            context += f"- {item.get('name')} ({item.get('id')}): ${item.get('price')}. Sizes: {sizes_str}. Stock: {item.get('stock')}\n"
                
        # Handle pagination if the catalog is larger than 1MB
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            for item in response.get('Items', []):
                category = item.get('category', 'Uncategorized')
                if filter_category and category != filter_category:
                    continue
                sizes_list = item.get('sizes', [])
                sizes_str = ', '.join(sizes_list) if isinstance(sizes_list, list) else sizes_list
                context += f"- {item.get('name')} ({item.get('id')}): ${item.get('price')}. Sizes: {sizes_str}. Stock: {item.get('stock')}\n"
                
        return context
        
    except Exception as e:
        logger.error(f"Failed to load products database from AWS DynamoDB: {e}")
        return "Catalog Out of Sync"
