from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db import models
from nrc_data.models import ReactorStatus
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from typing import Optional

class Command(BaseCommand):
    help = "Populates the database with NRC reactor status data from 1999-2025"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-year',
            type=int,
            default=1999,
            help='Starting year for data scraping (default: 1999)',
        )
        parser.add_argument(
            '--end-year', 
            type=int,
            default=2025,
            help='Ending year for data scraping (default: 2025)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Delay between requests in seconds (default: 2.0)',
        )
        parser.add_argument(
            '--resume-from',
            type=str,
            help='Resume from specific date (YYYYMMDD format)',
        )
        parser.add_argument(
            '--max-dates',
            type=int,
            help='Maximum number of dates to process (for testing)',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed logging including failed dates',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what dates would be processed without actually scraping',
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.setup_session()
        
        start_year = options['start_year']
        end_year = options['end_year']
        delay = options['delay']
        resume_from = options['resume_from']
        max_dates = options['max_dates']
        clear_existing = options['clear_existing']
        verbose = options['verbose']
        dry_run = options['dry_run']
        
        # Store verbose flag for use in other methods
        self._verbose = verbose

        # Clear existing data if requested
        if clear_existing and not dry_run:
            self.stdout.write("Clearing existing reactor status data...")
            ReactorStatus.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        # Generate date range
        dates = self.generate_date_range(start_year, end_year)
        
        # Filter dates if resuming
        if resume_from:
            dates = [d for d in dates if d >= resume_from]
            self.stdout.write(f"Resuming from {resume_from}")
        
        # Limit for testing
        if max_dates:
            dates = dates[:max_dates]
            self.stdout.write(f"Limited to {max_dates} dates for testing")

        total_dates = len(dates)
        self.stdout.write(f"Processing {total_dates} dates from {start_year} to {end_year}")
        
        # Dry run - just show what would be processed
        if dry_run:
            self.stdout.write(f"\n🔍 DRY RUN - Showing first 20 dates that would be processed:")
            for i, date_str in enumerate(dates[:20]):
                weekday_name = datetime.strptime(date_str, '%Y%m%d').strftime('%A')
                self.stdout.write(f"  {i+1:3d}. {date_str} ({weekday_name})")
            if len(dates) > 20:
                self.stdout.write(f"  ... and {len(dates) - 20} more dates")
            return
        
        # Process dates
        successful = 0
        failed = 0
        total_records = 0
        missing_dates = []
        error_dates = []
        
        for i, date_str in enumerate(dates, 1):
            if verbose:
                weekday_name = datetime.strptime(date_str, '%Y%m%d').strftime('%A')
                self.stdout.write(f"Progress: {i:4d}/{total_dates} - Processing {date_str} ({weekday_name})...", ending=" ")
            else:
                self.stdout.write(f"Progress: {i:4d}/{total_dates} - Processing {date_str}...", ending=" ")
            
            year = date_str[:4]
            reactor_df = self.fetch_nrc_reactor_status(year, date_str)
            
            if reactor_df is not None and not reactor_df.empty:
                saved_count = self.save_dataframe_to_db(reactor_df, date_str)
                if saved_count > 0:
                    successful += 1
                    total_records += saved_count
                    self.stdout.write(self.style.SUCCESS(f"✓ {saved_count} records"))
                else:
                    self.stdout.write(self.style.WARNING("- no new records"))
            else:
                failed += 1
                missing_dates.append(date_str)
                if verbose:
                    self.stdout.write(self.style.ERROR("✗ no data"))
                else:
                    self.stdout.write("- no data")
            
            # Progress summary every 50 dates
            if i % 50 == 0:
                self.stdout.write("\n--- Progress Update ---")
                self.stdout.write(f"Processed: {i}/{total_dates}")
                self.stdout.write(f"Successful: {successful}, Failed: {failed}")
                self.stdout.write(f"Total records added: {total_records:,}")
                if verbose and missing_dates[-10:]:  # Show last 10 missing dates
                    self.stdout.write(f"Recent missing dates: {', '.join(missing_dates[-10:])}")
                self.stdout.write("---")
            
            # Be respectful to the server
            time.sleep(delay)
        
        # Final summary
        self.stdout.write(self.style.SUCCESS(f"\n🎉 Seeding completed!"))
        self.stdout.write(f"Total dates processed: {i}")
        self.stdout.write(f"Successful: {successful}, Failed: {failed}")
        self.stdout.write(f"Total records added: {total_records:,}")
        
        # Show missing dates analysis
        if missing_dates:
            self.stdout.write(f"\n⚠️  Missing Data Analysis:")
            self.stdout.write(f"Total missing dates: {len(missing_dates)}")
            
            # Group missing dates by month
            missing_by_month = {}
            for date_str in missing_dates:
                month_key = date_str[:6]  # YYYYMM
                if month_key not in missing_by_month:
                    missing_by_month[month_key] = []
                missing_by_month[month_key].append(date_str)
            
            for month, dates in sorted(missing_by_month.items()):
                month_name = datetime.strptime(month + "01", '%Y%m%d').strftime('%B %Y')
                self.stdout.write(f"  {month_name}: {len(dates)} missing dates")
                if verbose:
                    self.stdout.write(f"    {', '.join(dates)}")
        
        # Show database stats
        self.show_database_stats()

    def setup_session(self):
        """Set up requests session with proper headers."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def generate_date_range(self, start_year: int, end_year: int):
        """Generate all dates to scrape (including weekends)."""
        dates = []
        
        for year in range(start_year, end_year + 1):
            start_date = datetime(year, 1, 1)
            
            # Don't go beyond today for current year
            if year == datetime.now().year:
                end_date = datetime.now()
            else:
                end_date = datetime(year, 12, 31)
            
            current_date = start_date
            while current_date <= end_date:
                # Include ALL days - NRC publishes on weekends too!
                date_str = current_date.strftime("%Y%m%d")
                dates.append(date_str)
                
                current_date += timedelta(days=1)
        
        return dates

    def fetch_nrc_reactor_status(self, year: str, date: str) -> Optional[pd.DataFrame]:
        """
        Fetch reactor status data using the EXACT same approach as Extract.ipynb
        
        Args:
            year: Year as string (e.g., '2025')
            date: Date as string in YYYYMMDD format (e.g., '20250107')
            
        Returns:
            pandas DataFrame or None if failed
        """
        url = f"https://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/{year}/{date}ps.html"
        
        try:
            response = requests.get(url, timeout=60)  # Increased timeout
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Store more detailed error info for debugging
            if hasattr(self, '_verbose') and self._verbose:
                if "404" in str(e):
                    self.stdout.write(self.style.WARNING(f"No report published for {date} - 404 error"))
                elif "timeout" in str(e).lower():
                    self.stdout.write(self.style.ERROR(f"Timeout fetching {date}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Network error for {date}: {e}"))
            return None

        try:
            # Use exact same approach as Extract.ipynb
            soup = BeautifulSoup(response.text, 'lxml')

            # Debug: Check what we found
            all_tables = soup.find_all('table', class_='power')
            if hasattr(self, '_verbose') and self._verbose:
                self.stdout.write(f"Found {len(all_tables)} table(s) on {date}")

            # Try to find 6-column tables first (preferred format)
            all_rows = []
            six_col_tables = 0
            for i, table in enumerate(all_tables):
                rows = table.find_all('tr')[1:]  # Skip header
                six_col_rows = []
                for row in rows:
                    cells = [td.get_text(strip=True) for td in row.find_all('td')]
                    if len(cells) == 6:
                        all_rows.append(cells)
                        six_col_rows.append(cells)
                
                if six_col_rows:
                    six_col_tables += 1
                    if hasattr(self, '_verbose') and self._verbose:
                        self.stdout.write(f"  Table {i+1}: {len(six_col_rows)} rows with 6 columns")

            # If no 6-column tables found, try 2-column tables (simplified format)
            if not all_rows:
                if hasattr(self, '_verbose') and self._verbose:
                    self.stdout.write(f"No 6-column tables found, trying 2-column format...")
                
                two_col_tables = 0
                for i, table in enumerate(all_tables):
                    rows = table.find_all('tr')[1:]  # Skip header
                    two_col_rows = []
                    for row in rows:
                        cells = [td.get_text(strip=True) for td in row.find_all('td')]
                        if len(cells) == 2:
                            # Convert 2-column to 6-column format with defaults
                            unit, power = cells
                            expanded_row = [unit, power, '', '', '', '']  # Add empty fields for Down, Reason, Change, Scrams
                            all_rows.append(expanded_row)
                            two_col_rows.append(expanded_row)
                    
                    if two_col_rows:
                        two_col_tables += 1
                        if hasattr(self, '_verbose') and self._verbose:
                            self.stdout.write(f"  Table {i+1}: {len(two_col_rows)} rows with 2 columns (converted to 6)")

            if not all_rows:
                if hasattr(self, '_verbose') and self._verbose:
                    self.stdout.write(self.style.WARNING(f"No reactor tables found for {date} (found {len(all_tables)} tables total)"))
                return None

            df = pd.DataFrame(all_rows, columns=['Unit', 'Power', 'Down', 'Reason', 'Change', 'Scrams'])
            df.replace('', pd.NA, inplace=True)
            
            if hasattr(self, '_verbose') and self._verbose:
                format_type = "6-column" if six_col_tables > 0 else "2-column"
                self.stdout.write(f"Successfully parsed {len(df)} reactor rows for {date} using {format_type} format")
            
            return df
            
        except Exception as e:
            if hasattr(self, '_verbose') and self._verbose:
                self.stdout.write(self.style.ERROR(f"Parsing error for {date}: {e}"))
            return None

    def normalize_unit_name(self, unit_name: str) -> str:
        """
        Normalize reactor unit names to a consistent format within 30-character limit.
        
        Args:
            unit_name: Raw unit name from NRC data
            
        Returns:
            Normalized unit name in consistent format (≤30 chars)
        """
        if not unit_name:
            return unit_name
        
        # First, aggressively clean whitespace
        normalized = ' '.join(unit_name.strip().split())  # Remove extra spaces
        normalized = normalized.title()  # Convert to title case
        
        # Handle specific formatting rules for known plants
        replacements = {
            # Fix common abbreviations and capitalizations
            'D.c. Cook': 'D.C. Cook',
            'D.C. Cook': 'D.C. Cook',  # Keep as is if already correct
            'Fitzpatrick': 'FitzPatrick',
            'Lasalle': 'LaSalle',
            'Mcguire': 'McGuire',  # Fix McGuire capitalization
            'Mcguire 1': 'McGuire 1',
            'Mcguire 2': 'McGuire 2',
            
            # Handle variations in plant names to match region mapping
            'Cook 1': 'D.C. Cook 1',  # Expand Cook to D.C. Cook
            'Cook 2': 'D.C. Cook 2',
            'Davis Besse': 'Davis-Besse',  # Add hyphen for consistency
            'Davis Besse 1': 'Davis-Besse 1',
            
            # Fix state abbreviations in names
            'Saint Lucie': 'Saint Lucie',  # Keep as is
            'St. Lucie': 'Saint Lucie',   # Standardize to full form
            
            # Handle Columbia Generating Station variations
            'Columbia Generating': 'Columbia Generating Station',  # Expand to full name
            'Columbia Generating Station': 'Columbia Generating Station',  # Keep as is
            
            # Handle River Bend variations
            'River Bend 1': 'River Bend Station 1',
            'River Bend Station 1': 'River Bend Station 1',  # Keep as is
            
            # Handle numbered units consistently (these are already correct but ensure consistency)
            ' 1': ' 1',
            ' 2': ' 2',  
            ' 3': ' 3',
            ' 4': ' 4',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Handle special cases for plants with unique naming
        special_cases = {
            'Fitzpatrick 1': 'FitzPatrick',  # Remove the "1" suffix if present
            'Three Mile Island': 'Three Mile Island 1',  # Add "1" if missing
            'Clinton 1': 'Clinton',  # Remove "1" from Clinton
            'Cooper 1': 'Cooper',    # Remove "1" from Cooper
            'Monticello 1': 'Monticello',  # Remove "1" from Monticello
            'Summer 1': 'Summer',    # Remove "1" from Summer
            'Callaway 1': 'Callaway',  # Remove "1" from Callaway
        }
        
        for old, new in special_cases.items():
            if normalized == old:
                normalized = new
                break
        
        # CRITICAL: Ensure result fits in 30-character database limit
        if len(normalized) > 30:
            # Debug logging for length issues
            if hasattr(self, '_verbose') and self._verbose:
                self.stdout.write(self.style.WARNING(f"Unit name too long ({len(normalized)} chars): '{normalized}'"))
            
            # If still too long after normalization, truncate with warning
            truncated = normalized[:30].rstrip()  # Remove trailing spaces after truncation
            if hasattr(self, '_verbose') and self._verbose:
                self.stdout.write(self.style.ERROR(f"    Truncated: '{normalized}' -> '{truncated}'"))
            normalized = truncated
        
        return normalized

    def save_dataframe_to_db(self, df: pd.DataFrame, date_str: str) -> int:
        """Convert DataFrame to Django models and save."""
        saved_count = 0
        report_date = datetime.strptime(date_str, '%Y%m%d').date()
        
        # Determine region based on table order (Region 1, 2, 3, 4)
        region_mapping = {
            'Beaver Valley': 'I', 'Calvert Cliffs': 'I', 'FitzPatrick': 'I', 'Ginna': 'I',
            'Hope Creek': 'I', 'Limerick': 'I', 'Millstone': 'I', 'Nine Mile Point': 'I',
            'Peach Bottom': 'I', 'Salem': 'I', 'Seabrook': 'I', 'Susquehanna': 'I',
            'Browns Ferry': 'II', 'Brunswick': 'II', 'Catawba': 'II', 'Farley': 'II',
            'Harris': 'II', 'Hatch': 'II', 'McGuire': 'II', 'North Anna': 'II',
            'Oconee': 'II', 'Robinson': 'II', 'Saint Lucie': 'II', 'Sequoyah': 'II',
            'Summer': 'II', 'Surry': 'II', 'Turkey Point': 'II', 'Vogtle': 'II',
            'Watts Bar': 'II', 'Braidwood': 'III', 'Byron': 'III', 'Clinton': 'III',
            'D.C. Cook': 'III', 'Davis-Besse': 'III', 'Dresden': 'III', 'Fermi': 'III',
            'LaSalle': 'III', 'Monticello': 'III', 'Perry': 'III', 'Point Beach': 'III',
            'Prairie Island': 'III', 'Quad Cities': 'III', 'Arkansas Nuclear': 'IV',
            'Callaway': 'IV', 'Columbia Generating Station': 'IV', 'Comanche Peak': 'IV',
            'Cooper': 'IV', 'Diablo Canyon': 'IV', 'Grand Gulf': 'IV', 'Palo Verde': 'IV',
            'River Bend Station': 'IV', 'South Texas': 'IV', 'Waterford': 'IV', 'Wolf Creek': 'IV'
        }

        with transaction.atomic():
            for _, row in df.iterrows():
                try:
                    # Normalize unit name for consistency
                    normalized_unit = self.normalize_unit_name(row['Unit'])
                    
                    # Debug: Show normalization if unit name changed
                    if hasattr(self, '_verbose') and self._verbose and normalized_unit != row['Unit']:
                        self.stdout.write(f"    Normalized: '{row['Unit']}' -> '{normalized_unit}'")
                    
                    # Check unit name length for debugging
                    if len(normalized_unit) > 30:
                        self.stdout.write(self.style.ERROR(f"    ERROR: Unit name too long: '{normalized_unit}' ({len(normalized_unit)} chars)"))
                        continue  # Skip this record
                    
                    # Determine region using normalized name
                    region = 'I'  # default
                    for plant_name, plant_region in region_mapping.items():
                        if plant_name.lower() in normalized_unit.lower():
                            region = plant_region
                            break
                    
                    # Parse data
                    power = int(row['Power']) if pd.notna(row['Power']) else 0
                    
                    # Parse down date
                    down_date = None
                    if pd.notna(row['Down']) and row['Down']:
                        try:
                            down_date = datetime.strptime(row['Down'], '%m/%d/%Y').date()
                        except:
                            pass
                    
                    # Parse other fields
                    reason = row['Reason'] if pd.notna(row['Reason']) else None
                    changed = bool(pd.notna(row['Change']) and '*' in str(row['Change']))
                    scrams = int(row['Scrams']) if pd.notna(row['Scrams']) and str(row['Scrams']).isdigit() else None
                    
                    reactor_status, created = ReactorStatus.objects.get_or_create(
                        report_date=report_date,
                        unit=normalized_unit,  # Use normalized unit name
                        defaults={
                            'power': power,
                            'down_date': down_date,
                            'reason': reason,
                            'changed': changed,
                            'scrams': scrams,
                            'region': region
                        }
                    )
                    
                    if created:
                        saved_count += 1
                        
                except Exception as e:
                    # More detailed error logging
                    unit_info = f"'{row['Unit']}'"
                    if 'normalized_unit' in locals():
                        unit_info += f" (normalized: '{normalized_unit}', {len(normalized_unit)} chars)"
                    self.stdout.write(self.style.ERROR(f"Error saving {unit_info}: {e}"))
        
        return saved_count

    def show_database_stats(self):
        """Display statistics about the current database."""
        total_records = ReactorStatus.objects.count()
        
        if total_records == 0:
            self.stdout.write("No data in database.")
            return
        
        date_range = ReactorStatus.objects.aggregate(
            min_date=models.Min('report_date'),
            max_date=models.Max('report_date')
        )
        
        unique_units = ReactorStatus.objects.values('unit').distinct().count()
        
        # Recent data sample
        recent_data = ReactorStatus.objects.filter(
            report_date=ReactorStatus.objects.aggregate(
                max_date=models.Max('report_date')
            )['max_date']
        )[:5]
        
        self.stdout.write(f"\n📊 Database Statistics:")
        self.stdout.write(f"Total records: {total_records:,}")
        self.stdout.write(f"Date range: {date_range['min_date']} to {date_range['max_date']}")
        self.stdout.write(f"Unique reactor units: {unique_units}")
        
        if recent_data:
            self.stdout.write(f"\nSample recent data:")
            for reactor in recent_data:
                reason_str = f" ({reactor.reason})" if reactor.reason else ""
                self.stdout.write(f"  {reactor.unit}: {reactor.power}%{reason_str}")
    