# dashboard.py
import sys
import plotext as plt
from metrics_base import MetricFetcher
import my_metrics # Import your custom metrics

# CONFIG
PROMETHEUS_URL = "http://localhost:9090"

def draw_chart(metric_class):
    fetcher = MetricFetcher(PROMETHEUS_URL)
    
    print(f"Fetching {metric_class.title}...")
    x, y = fetcher.get_data(metric_class)

    if not x:
        print("No data received from Prometheus.")
        return

    plt.clear_figure()
    plt.theme('dark')
    
    # Plotting
    plt.plot(x, y, marker="dot", color="green")
    
    # Styling
    plt.title(metric_class.title)
    plt.ylabel(metric_class.unit)
    plt.xlabel("Time")
    plt.grid(True, True)
    plt.show()

if __name__ == "__main__":
    # Create a mapping of keywords to classes
    # This lets you run: python dashboard.py cpu
    available_metrics = {
        "cpu": my_metrics.CPULoadMetric,
        "deploy": my_metrics.DeploymentCountMetric,
        "mem": my_metrics.MemoryUsageMetric
    }

    if len(sys.argv) < 2 or sys.argv[1] not in available_metrics:
        print("Please specify a metric to plot:")
        print(f"Options: {', '.join(available_metrics.keys())}")
        sys.exit(1)

    choice = sys.argv[1]
    selected_metric = available_metrics[choice]
    
    draw_chart(selected_metric)
