#!/usr/bin/env python3
"""Example usage of the Auto Status Report application."""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.app import AutoStatusReportApp


def main():
    """Demonstrate the Auto Status Report application."""
    
    print("🚀 Auto Status Report - Example Usage")
    print("=" * 50)
    
    try:
        # Initialize the application
        app = AutoStatusReportApp()
        
        # Test connections
        print("Testing connections...")
        if not app.test_connections():
            print("❌ Connection tests failed. Please check your .env file.")
            return
        print("✅ All connections successful!")
        
        # List repositories
        print("\n📁 Available repositories:")
        repos = app.list_repositories()
        for i, repo in enumerate(repos[:5], 1):  # Show first 5
            print(f"  {i}. {repo}")
        if len(repos) > 5:
            print(f"  ... and {len(repos) - 5} more")
        
        # Generate a quick report
        print("\n📊 Generating 3-day status report...")
        status_report = app.generate_status_report(
            days_back=3,
            include_llm_summary=True
        )
        
        # Print summary
        app.print_summary(status_report)
        
        # Save report to file
        output_file = "example_report.md"
        app.report_generator.save_report(
            status_report,
            output_file,
            format="markdown",
            include_llm_summary=True
        )
        print(f"\n💾 Full report saved to: {output_file}")
        
        # Show repository stats for the most active repo
        if status_report.most_active_repos:
            most_active = status_report.most_active_repos[0]
            print(f"\n📈 Detailed stats for {most_active}:")
            stats = app.get_repository_stats(most_active, days_back=7)
            print(f"  Commits: {stats['total_commits']}")
            print(f"  Lines added: {stats['total_additions']:,}")
            print(f"  Lines deleted: {stats['total_deletions']:,}")
            print(f"  Files changed: {stats['total_files_changed']}")
            print(f"  Avg commits/day: {stats['average_commits_per_day']:.1f}")
        
        print("\n🎉 Example completed successfully!")
        print("\nNext steps:")
        print("1. Try different commands: python main.py --help")
        print("2. Generate reports for specific repositories")
        print("3. Set up automated reporting on your Jenkins server")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your .env file is configured correctly")
        print("2. Check that your GitHub token has the right permissions")
        print("3. Verify your OpenAI API key is valid")
        print("4. Run 'python main.py test' to diagnose issues")


if __name__ == "__main__":
    main()
