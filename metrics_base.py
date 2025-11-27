# metrics_base.py
from datetime import datetime, timedelta
from prometheus_api_client import PrometheusConnect

class MetricFetcher:
    def __init__(self, url):
        self.prom = PrometheusConnect(url=url, disable_ssl=True)

    def get_data(self, metric_class, minutes=60):
        """
        Takes a Metric Class (from my_metrics.py), runs the query,
        and returns cleaned X and Y lists.
        """
        start_time = datetime.now() - timedelta(minutes=minutes)
        end_time = datetime.now()

        # Fetch data
        result = self.prom.custom_query_range(
            query=metric_class.query,
            start_time=start_time,
            end_time=end_time,
            step='1m'
        )

        if not result:
            return None, None

        # Extract the first series found
        # (For more complex dashboards, you might handle multiple series here)
        data_points = result[0]['values']

        # Process X Axis (Time)
        timestamps = [datetime.fromtimestamp(float(x[0])) for x in data_points]
        x_labels = [dt.strftime("%H:%M") for dt in timestamps]

        # Process Y Axis (Values)
        y_values = []
        for x in data_points:
            val = float(x[1])
            # Check if the metric class has a custom transform function
            if hasattr(metric_class, 'transform'):
                val = metric_class.transform(val)
            y_values.append(val)

        return x_labels, y_values
