import os
import django
import pandas as pd
import plotly.graph_objects as go
import boto3
from io import BytesIO
from datetime import timedelta
from prophet import Prophet

# Django setup (optional if already configured)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nucleartimeseries_api.settings")
django.setup()

from nrc_data.models import ReactorStatus

# AWS S3 config (update these)
S3_BUCKET_NAME = "nuclearforecast"
S3_FORECAST_FOLDER = "forecasts/"
AWS_REGION = "us-east-1"  # Change as needed

def generate_and_upload_forecast(unit_name):
    # Step 1: Load data
    qs = ReactorStatus.objects.filter(unit__icontains=unit_name).order_by("report_date")
    if not qs.exists():
        print(f"No data found for unit: {unit_name}")
        return None

    df = pd.DataFrame(qs.values("report_date", "power"))
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
    latest_date = df_prophet["ds"].max()
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
    html_buffer = BytesIO()
    fig.write_html(html_buffer)
    html_buffer.seek(0)

    # Step 7: Upload to S3
    s3 = boto3.client("s3", region_name=AWS_REGION)
    filename = f"{S3_FORECAST_FOLDER}{unit_name.replace(' ', '_')}_forecast.html"
    s3.upload_fileobj(html_buffer, S3_BUCKET_NAME, filename, ExtraArgs={'ContentType': 'text/html'})

    # Step 8: Return public URL
    url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{filename}"
    print(f"Forecast uploaded to: {url}")
    return url
