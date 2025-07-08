from celery import shared_task
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Max
from nrc_data.models import ReactorStatus
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def fetch_latest_nrc_data():
    latest = ReactorStatus.objects.aggregate(Max('report_date'))['report_date__max']
    logger.info(f"Latest date: {latest}")
    if not latest:
        print("No data found.")
        return
    
    next_date = latest + timedelta(days=1)
    today = now().date()

    if next_date > today:
        print("No new date to fetch yet")
        return
    
    date_str = next_date.strftime("%Y%m%d")

    print(f"Fetching data for {date_str}")

    try:
        call_command('seed',
        '--start-year', str(next_date.year),
        '--end-year', str(next_date.year),
        '--max-dates', str(1),
        '--resume-from', str(date_str),
        '--delay', str(0.5),
        '--verbose'
        )   
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
    
    print(f"Data fetched and saved for {date_str}")



