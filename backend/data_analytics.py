"""
Data Analytics for SeeClickFix Issues

This script processes and analyzes data from the seeclickfix_issues collection
and returns summary, rating, and status for each data point.
"""
import os
import sys
import csv
from typing import List, Dict, Any, Optional

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import get_database, get_collection
from dotenv import load_dotenv

load_dotenv()


def get_all_issues(
    limit: Optional[int] = None,
    status_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve all issues from MongoDB with optional filters.
    
    Args:
        limit: Maximum number of issues to return
        status_filter: Filter by status (e.g., "Open", "Acknowledged", "Closed")
    
    Returns:
        List of issue documents
    """
    collection = get_collection("seeclickfix_issues")
    
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    cursor = collection.find(query)
    
    if limit:
        cursor = cursor.limit(limit)
    
    return list(cursor)


def extract_summary_rating_status(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract summary, rating, and status from each issue.
    
    Args:
        issues: List of issue documents
    
    Returns:
        List of extracted data (summary, rating, status)
    """
    extracted = []
    
    for issue in issues:
        extracted.append({
            "scf_id": issue.get("scf_id"),
            "summary": issue.get("summary"),
            "rating": issue.get("rating"),
            "status": issue.get("status")
        })
    
    return extracted


def analyze_issues() -> Dict[str, Any]:
    """
    Perform comprehensive analytics on the issues data.
    
    Returns:
        Dictionary containing analytics results
    """
    all_issues = get_all_issues()
    
    if not all_issues:
        return {
            "total_issues": 0,
            "message": "No issues found in database"
        }
    
    # Extract key fields
    extracted_data = extract_summary_rating_status(all_issues)
    
    # Status distribution
    status_counts = {}
    for issue in all_issues:
        status = issue.get("status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Rating distribution
    rating_counts = {}
    for issue in all_issues:
        rating = issue.get("rating")
        if rating is not None:
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
    
    # Average rating
    ratings = [issue.get("rating") for issue in all_issues if issue.get("rating") is not None]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    return {
        "total_issues": len(all_issues),
        "extracted_data": extracted_data,
        "status_distribution": status_counts,
        "rating_distribution": rating_counts,
        "average_rating": round(avg_rating, 2)
    }


def get_issues_by_status(status: str) -> List[Dict[str, Any]]:
    """
    Get all issues filtered by status.
    
    Args:
        status: Status to filter by
    
    Returns:
        List of issues with summary, rating, status
    """
    issues = get_all_issues(status_filter=status)
    return extract_summary_rating_status(issues)


def print_analytics():
    """Print analytics results to console."""
    print("=" * 60)
    print("SeeClickFix Data Analytics")
    print("=" * 60)
    
    analytics = analyze_issues()
    
    print(f"\nTotal Issues: {analytics.get('total_issues', 0)}")
    print(f"Average Rating: {analytics.get('average_rating', 0)}")
    
    print("\n--- Status Distribution ---")
    for status, count in analytics.get("status_distribution", {}).items():
        print(f"  {status}: {count}")
    
    print("\n--- Rating Distribution ---")
    for rating, count in analytics.get("rating_distribution", {}).items():
        print(f"  Rating {rating}: {count}")
    
    print("\n--- Sample Issues (first 10) ---")
    extracted = analytics.get("extracted_data", [])[:10]
    for issue in extracted:
        print(f"  [{issue['status']}] Rating: {issue['rating']} - {issue['summary'][:50]}...")
    
    print("\n--- All Issues Summary ---")
    for issue in analytics.get("extracted_data", []):
        print(f"Summary: {issue['summary']}")
        print(f"Rating: {issue['rating']}")
        print(f"Status: {issue['status']}")
        print("-" * 40)


def export_unique_to_csv(output_file: str = "unique_data.csv") -> Dict[str, Any]:
    """
    Export unique summaries and unique ratings to a CSV file.
    
    Args:
        output_file: Path to output CSV file
    
    Returns:
        Dictionary with export results
    """
    all_issues = get_all_issues()
    
    if not all_issues:
        return {
            "success": False,
            "message": "No issues found in database"
        }
    
    # Get unique summaries
    unique_summaries = set()
    for issue in all_issues:
        summary = issue.get("summary")
        if summary:
            unique_summaries.add(summary)
    
    # Get unique ratings
    unique_ratings = set()
    for issue in all_issues:
        rating = issue.get("rating")
        if rating is not None:
            unique_ratings.add(rating)
    
    unique_ratings = sorted(list(unique_ratings))
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write unique summaries
        writer.writerow(["Unique Summaries"])
        for summary in sorted(unique_summaries):
            writer.writerow([summary])
        
        # Add spacing
        writer.writerow([])
        writer.writerow([])
        
        # Write unique ratings
        writer.writerow(["Unique Ratings"])
        for rating in unique_ratings:
            writer.writerow([rating])
    
    print(f"\nExported to {output_file}")
    print(f"  - Unique Summaries: {len(unique_summaries)}")
    print(f"  - Unique Ratings: {len(unique_ratings)}")
    
    return {
        "success": True,
        "output_file": output_file,
        "unique_summaries_count": len(unique_summaries),
        "unique_ratings_count": len(unique_ratings),
        "unique_summaries": sorted(list(unique_summaries)),
        "unique_ratings": unique_ratings
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze SeeClickFix data")
    parser.add_argument("--status", type=str, help="Filter by status")
    parser.add_argument("--limit", type=int, help="Limit number of results")
    parser.add_argument("--print-all", action="store_true", help="Print all issues")
    parser.add_argument("--csv", type=str, help="Export unique summaries and ratings to CSV file")
    
    args = parser.parse_args()
    
    if args.csv:
        export_unique_to_csv(args.csv)
    elif args.status:
        issues = get_issues_by_status(args.status)
        print(f"\nIssues with status '{args.status}':")
        for issue in issues:
            print(f"  - {issue['summary']} (Rating: {issue['rating']}, Status: {issue['status']})")
    elif args.print_all:
        print_analytics()
    else:
        analytics = analyze_issues()
        print(f"Total: {analytics['total_issues']} issues")
        print(f"Average Rating: {analytics['average_rating']}")
        print("\nExtracted Data (summary, rating, status):")
        for issue in analytics.get("extracted_data", [])[:20]:
            print(f"  Summary: {issue['summary']}")
            print(f"  Rating: {issue['rating']}")
            print(f"  Status: {issue['status']}")
            print()
