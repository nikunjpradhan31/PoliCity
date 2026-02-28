"""CSV parser utility for budget uploads."""

import csv
import io
from typing import List, Optional

from app.models.budget import BudgetItem
from app.core.logging import logger


class CSVParseError(Exception):
    """Exception raised for CSV parsing errors."""
    pass


def parse_budget_csv(
    csv_content: str,
    city: str,
    year: int,
) -> dict:
    """
    Parse CSV content for budget data.
    
    Expected CSV format:
    category,amount,description
    Road Repair,50000,Annual road maintenance
    Pothole Fixing,25000,Priority pothole repairs
    ...
    
    Args:
        csv_content: CSV content as string
        city: City name
        year: Budget year
        
    Returns:
        Parsed budget data with total
        
    Raises:
        CSVParseError: If CSV is invalid
    """
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
        
        items: List[BudgetItem] = []
        total_budget = 0.0
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
            # Validate required fields
            category = row.get("category", "").strip()
            amount_str = row.get("amount", "").strip()
            description = row.get("description", "").strip()
            
            if not category:
                raise CSVParseError(
                    f"Missing category in row {row_num}"
                )
            
            if not amount_str:
                raise CSVParseError(
                    f"Missing amount in row {row_num}"
                )
            
            try:
                amount = float(amount_str)
            except ValueError:
                raise CSVParseError(
                    f"Invalid amount '{amount_str}' in row {row_num}"
                )
            
            if amount < 0:
                raise CSVParseError(
                    f"Negative amount in row {row_num}"
                )
            
            items.append(BudgetItem(
                category=category,
                amount=amount,
                description=description or None,
            ))
            
            total_budget += amount
        
        if not items:
            raise CSVParseError("CSV contains no valid budget items")
        
        logger.info(
            f"Parsed budget CSV: {len(items)} items, "
            f"total ${total_budget}"
        )
        
        return {
            "city": city,
            "year": year,
            "total_budget": total_budget,
            "items": items,
        }
        
    except csv.Error as e:
        raise CSVParseError(f"CSV parsing error: {str(e)}")


def validate_budget_csv_format(csv_content: str) -> bool:
    """
    Validate CSV format has required columns.
    
    Args:
        csv_content: CSV content as string
        
    Returns:
        True if valid, False otherwise
    """
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
        fieldnames = reader.fieldnames or []
        
        required_fields = {"category", "amount"}
        
        return required_fields.issubset(set(fieldnames))
        
    except Exception:
        return False
