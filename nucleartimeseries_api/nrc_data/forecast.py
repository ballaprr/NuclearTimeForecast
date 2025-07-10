import os
import django
import pandas as pd
import plotly.graph_objects as go
import boto3
from io import BytesIO, StringIO
from datetime import timedelta
from prophet import Prophet
from nrc_data.models import Reactor, ReactorStatus, ReactorForecast
import pandas as pd
from nrc_data.outage_detection import detect_stub_outages_for_reactor
from django.conf import settings

# Django setup (optional if already configured)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nucleartimeseries_api.settings")
django.setup()

from nrc_data.models import ReactorStatus

def generate_and_upload_forecast(unit_name):
    # Step 1: Load data
    qs = ReactorStatus.objects.filter(unit=unit_name).order_by('report_date')
    df = pd.DataFrame(list(qs.values("report_date", "power")))
    if df.empty:
        raise ValueError(f"No data found for {unit_name}")
    
    df_prophet = df.rename(columns={"report_date": "ds", "power": "y"})

    # Step 2: Identify refueling outages (y == 0)
    refuel_days = df_prophet[df_prophet["y"] == 0]
    holidays = pd.DataFrame({
        "holiday": "refueling_outage",
        "ds": refuel_days["ds"],
        "lower_window": 0,
        "upper_window": 5
    })

    # Step 3: Train model
    model = Prophet(
        daily_seasonality=False,
        yearly_seasonality=True,
        weekly_seasonality=False,
        changepoint_prior_scale=0.5,
        holidays=holidays
    )
    model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    model.fit(df_prophet)

    # Step 4: Forecast
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    latest_date = pd.to_datetime(df_prophet['ds'].max())
    next_day = latest_date + timedelta(days=1)
    day30 = latest_date + timedelta(days=30)

    try:
        reactor_obj = Reactor.objects.get(name=unit_name)
    except Reactor.DoesNotExist:
        raise ValueError(f"Reactor with name '{unit_name}' not found")

    for day in [next_day, day30]:
        row = forecast[forecast['ds'] == day]
        if row.empty:
            continue

        # Upload forecast row to DB
        ReactorForecast.objects.update_or_create(
            reactor=reactor_obj,
            df=day,
            defaults={
                'yhat': row['yhat'].values[0],
                'yhat_lower': row['yhat_lower'].values[0],
                'yhat_upper': row['yhat_upper'].values[0],
            }
        )
    forecast_30 = forecast[forecast["ds"] > latest_date]

    # Step 5: Plot actual vs forecast
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_prophet['ds'], y=df_prophet['y'], mode='lines', name='Actual'))
    fig.add_trace(go.Scatter(x=forecast_30['ds'], y=forecast_30['yhat'], mode='lines', name='Forecast'))
    fig.add_trace(go.Scatter(x=forecast_30['ds'], y=forecast_30['yhat_upper'], mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=forecast_30['ds'], y=forecast_30['yhat_lower'], mode='lines', fill='tonexty', line=dict(width=1), showlegend=False))
    fig.update_layout(
        title=f"{unit_name} – Next 30 Day Forecast",
        xaxis_title="Date",
        yaxis_title="Power (%)",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        template="plotly_white"
    )

    # Step 6: Save to HTML in memory
    html_buffer = StringIO()
    fig.write_html(html_buffer)
    html_str = html_buffer.getvalue().encode("utf-8")  # Convert str to bytes
    html_bytes = BytesIO(html_str)

    # Step 7: Upload to S3
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    s3_path = f"{settings.S3_FORECAST_FOLDER}{unit_name.replace(' ', '_')}.html"
    try:
        s3.upload_fileobj(html_bytes, bucket, s3_path, ExtraArgs={'ContentType': 'text/html'})
    except Exception as e:
        print(f"❌ Failed to upload to S3 for {unit_name}: {e}")
        return

    # Step 8: Return public URL
    url = f"https://{bucket}.s3.amazonaws.com/{s3_path}"
    ReactorForecast.objects.filter(reactor=reactor_obj, df__in=[next_day, day30]).update(image_url=url)
    detect_stub_outages_for_reactor(reactor_obj)
    return url
