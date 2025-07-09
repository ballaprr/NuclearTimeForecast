from celery import shared_task
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Max
from nrc_data.models import ReactorStatus
from django.core.management import call_command
from forecast import generate_and_upload_forecast
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nucleartimeseries_api.settings")
django.setup()

from nrc_data.models import ReactorStatus

# from forecast import generate_and_upload_forecast
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
    
    updated_reactors = ReactorStatus.objects.filter(report_date=next_date).values_list('unit', flat=True).distinct()

    for reactor_name in updated_reactors:
        try:
            url = generate_and_upload_forecast(reactor_name)
            print(f"✅ Forecast uploaded for {reactor_name}: {url}")
        except Exception as e:
            print(f"❌ Forecast failed for {reactor_name}: {e}")

    print(f"Data fetched and saved for {date_str}")



