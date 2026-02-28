"""
SeeClickFix Data Points Uploader

This script fetches issues from the SeeClickFix API and uploads them to MongoDB.
It retrieves 200 data points per page and can process multiple pages.
"""
import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import sys

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import get_database, get_collection
from dotenv import load_dotenv

load_dotenv()


# SeeClickFix API configuration
SCF_BASE_URL = "https://seeclickfix.com/api/v2"
ISSUES_ENDPOINT = f"{SCF_BASE_URL}/issues"


def fetch_issues_page(page: int = 1, per_page: int = 200) -> Optional[Dict[str, Any]]:
    """
    Fetch a single page of issues from SeeClickFix API.
    
    Args:
        page: Page number (1-indexed)
        per_page: Number of issues per page (max 200)
    
    Returns:
        Dict containing issues and metadata, or None if request fails
    """
    params = {
        "page": page,
        "per_page": per_page
    }
    
    try:
        response = requests.get(ISSUES_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        return None


def transform_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform SeeClickFix issue data into a clean format for MongoDB.
    
    Args:
        issue: Raw issue data from SeeClickFix API
    
    Returns:
        Transformed issue data
    """
    # Extract reporter info
    reporter = issue.get("reporter", {})
    
    # Extract request type info
    request_type = issue.get("request_type", {})
    
    # Extract media info
    media = issue.get("media", {})
    
    # Extract point coordinates
    point = issue.get("point", {})
    coordinates = point.get("coordinates", [0, 0])
    
    transformed = {
        # Primary identifiers
        "scf_id": issue.get("id"),
        "status": issue.get("status"),
        "summary": issue.get("summary"),
        "description": issue.get("description"),
        "rating": issue.get("rating"),
        
        # Location data
        "latitude": issue.get("lat"),
        "longitude": issue.get("lng"),
        "address": issue.get("address"),
        "coordinates": {
            "type": "Point",
            "coordinates": coordinates
        },
        
        # Timestamps
        "created_at": issue.get("created_at"),
        "acknowledged_at": issue.get("acknowledged_at"),
        "closed_at": issue.get("closed_at"),
        "reopened_at": issue.get("reopened_at"),
        "updated_at": issue.get("updated_at"),
        
        # URLs and links
        "url": issue.get("url"),
        "html_url": issue.get("html_url"),
        
        # Request type info
        "request_type": {
            "id": request_type.get("id"),
            "title": request_type.get("title"),
            "organization": request_type.get("organization"),
            "url": request_type.get("url")
        },
        
        # Reporter info
        "reporter": {
            "id": reporter.get("id"),
            "name": reporter.get("name"),
            "role": reporter.get("role"),
            "html_url": reporter.get("html_url"),
            "civic_points": reporter.get("civic_points")
        },
        
        # Media info
        "media": {
            "video_url": media.get("video_url"),
            "image_full": media.get("image_full"),
            "image_square_100x100": media.get("image_square_100x100"),
            "representative_image_url": media.get("representative_image_url")
        },
        
        # Metadata
        "private_visibility": issue.get("private_visibility"),
        "imported_at": datetime.utcnow().isoformat()
    }
    
    return transformed


def upload_issues_to_mongo(issues: List[Dict[str, Any]]) -> int:
    """
    Upload issues to MongoDB.
    
    Args:
        issues: List of transformed issue data
    
    Returns:
        Number of issues uploaded
    """
    if not issues:
        return 0
    
    collection = get_collection("seeclickfix_issues")
    
    # Use upsert to avoid duplicates based on scf_id
    uploaded_count = 0
    for issue in issues:
        scf_id = issue.get("scf_id")
        if scf_id:
            result = collection.update_one(
                {"scf_id": scf_id},
                {"$set": issue},
                upsert=True
            )
            if result.upserted_id or result.modified_count:
                uploaded_count += 1
    
    return uploaded_count


def fetch_and_upload_page(page: int, per_page: int = 200) -> Dict[str, Any]:
    """
    Fetch a page of issues and upload to MongoDB.
    
    Args:
        page: Page number
        per_page: Number of issues per page
    
    Returns:
        Result dictionary with status and counts
    """
    print(f"Fetching page {page} with {per_page} issues per page...")
    
    data = fetch_issues_page(page, per_page)
    
    if not data:
        return {
            "success": False,
            "page": page,
            "message": "Failed to fetch data"
        }
    
    issues = data.get("issues", [])
    metadata = data.get("metadata", {})
    pagination = metadata.get("pagination", {})
    
    if not issues:
        return {
            "success": False,
            "page": page,
            "message": "No issues found"
        }
    
    # Transform issues
    transformed_issues = [transform_issue(issue) for issue in issues]
    
    # Upload to MongoDB
    uploaded = upload_issues_to_mongo(transformed_issues)
    
    print(f"  - Found {len(issues)} issues")
    print(f"  - Uploaded {uploaded} issues to MongoDB")
    
    return {
        "success": True,
        "page": page,
        "total_found": len(issues),
        "uploaded": uploaded,
        "total_entries": pagination.get("entries"),
        "total_pages": pagination.get("pages"),
        "next_page": pagination.get("next_page")
    }


def run_uploader(num_pages: int = 1, per_page: int = 200):
    """
    Run the uploader for specified number of pages.
    
    Args:
        num_pages: Number of pages to fetch (default 1)
        per_page: Issues per page (max 200)
    """
    print(f"Starting SeeClickFix Data Uploader")
    print(f"Target: {num_pages} pages × {per_page} issues = {num_pages * per_page} total")
    print("-" * 50)
    
    total_uploaded = 0
    successful_pages = 0
    
    for page in range(1, num_pages + 1):
        result = fetch_and_upload_page(page, per_page)
        
        if result.get("success"):
            total_uploaded += result.get("uploaded", 0)
            successful_pages += 1
            
            # Check if there are more pages
            if not result.get("next_page") and page < num_pages:
                print(f"No more pages available. Stopping at page {page}.")
                break
        else:
            print(f"Failed to process page {page}: {result.get('message')}")
    
    print("-" * 50)
    print(f"Completed: {successful_pages} pages, {total_uploaded} total issues uploaded")
    
    return {
        "total_uploaded": total_uploaded,
        "successful_pages": successful_pages
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload SeeClickFix issues to MongoDB")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to fetch")
    parser.add_argument("--per-page", type=int, default=200, help="Issues per page (max 200)")
    
    args = parser.parse_args()
    
    run_uploader(num_pages=args.pages, per_page=args.per_page)
