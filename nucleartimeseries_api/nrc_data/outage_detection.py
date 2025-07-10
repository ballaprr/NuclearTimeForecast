from datetime import timedelta
from nrc_data.models import ReactorStatus, ReactorForecast, StubOutage, Reactor


def detect_stub_outages_for_reactor(reactor_name, threshold_drops=5):
    print(f"Detecting stub outages for {reactor_name}")
    try:
        reactor = Reactor.objects.get(name=reactor_name)
    except Reactor.DoesNotExist:
        return

    latest_actual = ReactorStatus.objects.filter(unit=reactor_name).order_by('-report_date').first()
    if not latest_actual:
        print(f"⚠️ No actual data found for {reactor_name}")
        return
    print(f"Latest actual: {latest_actual.report_date}")
    forecast = ReactorForecast.objects.filter(
        reactor=reactor,
        df=latest_actual.report_date + timedelta(days=1)
    ).first()

    if not forecast:
        print(f"⚠️ No forecast found for {reactor_name} on {latest_actual.report_date}")
        return

    actual = latest_actual.power
    predicted = forecast.yhat

    drop = predicted - actual

    # We want to save stub outage even when the drop is less than the threshold
    print(f"📊 {reactor_name}: Predicted = {predicted}, Actual = {actual}, Drop = {drop}")
    if drop >= threshold_drops:
        StubOutage.objects.get_or_create(
            reactor=reactor, 
            date_detected=latest_actual.report_date,
            defaults={
                'description': f"Detected {drop:.1f}% drop vs forecast ({predicted:.1f} → {actual:.1f})",
                'auto_detected': True,
                'confirmed': False,
            },
            reactorstatus=latest_actual
        )