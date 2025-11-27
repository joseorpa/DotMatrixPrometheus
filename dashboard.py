# dashboard.py
"""
DotMatrixPrometheus - Terminal-based Prometheus metrics visualization.

Usage:
    python dashboard.py <metric_name> [options]
    python dashboard.py metric1 metric2 metric3   # Multiple metrics in grid
    python dashboard.py --list              # List all available metrics
    python dashboard.py --list-ingress      # List ingress-perf metrics only
    python dashboard.py --help              # Show help

Options:
    --url, -u     Prometheus URL (default: http://localhost:9090)
    --from, -f    Start datetime (e.g., "Nov 13 08:00", "2024-11-13 08:00")
    --to, -t      End datetime (e.g., "Nov 13 10:00", "10:00")
    --minutes, -m Minutes to look back from now (default: 60)
    --cols, -c    Number of columns for multi-metric grid (default: auto)

Metrics based on cloud-bulldozer/performance-dashboards:
- ingress-perf.jsonnet
- k8s-netperf.jsonnet
- kube-burner-report-ocp-wrapper.jsonnet
- etcd-on-cluster-dashboard.jsonnet
- ocp-performance.jsonnet
- ovn-dashboard.jsonnet
- hypershift-performance.jsonnet
"""

import sys
import argparse
import math
import plotext as plt
from metrics_base import MetricFetcher, parse_datetime, PrometheusConnectionError
import my_metrics  # Import your custom metrics

# CONFIG
DEFAULT_PROMETHEUS_URL = "http://localhost:9090"

# Color palette for multi-chart display
CHART_COLORS = ["green", "cyan", "yellow", "magenta", "red", "blue", "orange", "white"]


def calculate_grid(num_charts, cols=None):
    """Calculate optimal grid dimensions for displaying multiple charts."""
    if cols:
        rows = math.ceil(num_charts / cols)
        return rows, cols
    
    # Auto-calculate based on number of charts
    if num_charts == 1:
        return 1, 1
    elif num_charts == 2:
        return 1, 2
    elif num_charts <= 4:
        return 2, 2
    elif num_charts <= 6:
        return 2, 3
    elif num_charts <= 9:
        return 3, 3
    elif num_charts <= 12:
        return 3, 4
    else:
        cols = 4
        rows = math.ceil(num_charts / cols)
        return rows, cols


def fetch_metric_data(metric_class, fetcher, minutes, start_time, end_time):
    """Fetch data for a single metric."""
    x_labels, y = fetcher.get_data(
        metric_class,
        minutes=minutes,
        start_time=start_time,
        end_time=end_time
    )
    return x_labels, y


def draw_chart(metric_class, prometheus_url, minutes=60, start_time=None, end_time=None):
    """Fetch and draw a single chart for the given metric class."""
    fetcher = MetricFetcher(prometheus_url)
    
    # Build info message
    if start_time and end_time:
        time_info = f"from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}"
    elif start_time:
        time_info = f"from {start_time.strftime('%Y-%m-%d %H:%M')} to now"
    else:
        time_info = f"last {minutes} minutes"
    
    print(f"Fetching {metric_class.title} ({time_info})...")
    x_labels, y = fetcher.get_data(
        metric_class, 
        minutes=minutes,
        start_time=start_time,
        end_time=end_time
    )

    if not x_labels:
        print("No data received from Prometheus.")
        return

    plt.clear_figure()
    plt.theme('dark')
    
    # Use numeric indices for x-axis to avoid plotext date parsing issues
    x_indices = list(range(len(x_labels)))
    
    # Plotting with numeric x values
    plt.plot(x_indices, y, marker="dot", color="green")
    
    # Set custom x-axis labels (show subset to avoid crowding)
    num_labels = min(10, len(x_labels))  # Show at most 10 labels
    if len(x_labels) > num_labels:
        step = len(x_labels) // num_labels
        label_indices = list(range(0, len(x_labels), step))
        label_values = [x_labels[i] for i in label_indices]
    else:
        label_indices = x_indices
        label_values = x_labels
    
    plt.xticks(label_indices, label_values)
    
    # Build title with time range
    title = metric_class.title
    if start_time and end_time:
        title += f"\n{start_time.strftime('%Y-%m-%d %H:%M')} → {end_time.strftime('%H:%M')}"
    
    # Styling
    plt.title(title)
    plt.ylabel(metric_class.unit)
    plt.xlabel("Time")
    plt.grid(True, True)
    plt.show()


def draw_multi_chart(metric_classes, metric_names, prometheus_url, minutes=60, 
                     start_time=None, end_time=None, cols=None):
    """Fetch and draw multiple charts in a grid layout."""
    fetcher = MetricFetcher(prometheus_url)
    
    # Build info message
    if start_time and end_time:
        time_info = f"from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}"
    elif start_time:
        time_info = f"from {start_time.strftime('%Y-%m-%d %H:%M')} to now"
    else:
        time_info = f"last {minutes} minutes"
    
    num_metrics = len(metric_classes)
    rows, cols = calculate_grid(num_metrics, cols)
    
    print(f"\n📊 Fetching {num_metrics} metrics ({time_info})...")
    print(f"   Layout: {rows} rows × {cols} columns\n")
    
    # Fetch all data first
    all_data = []
    for i, (metric_class, metric_name) in enumerate(zip(metric_classes, metric_names)):
        print(f"   [{i+1}/{num_metrics}] {metric_class.title}...", end=" ", flush=True)
        x_labels, y = fetch_metric_data(metric_class, fetcher, minutes, start_time, end_time)
        if x_labels and y:
            all_data.append((metric_class, metric_name, x_labels, y))
            print("✓")
        else:
            all_data.append((metric_class, metric_name, None, None))
            print("✗ (no data)")
    
    print()  # Newline before chart
    
    # Clear figure and set up subplots
    plt.clear_figure()
    plt.theme('dark')
    plt.subplots(rows, cols)
    
    # Draw each chart
    for i, (metric_class, metric_name, x_labels, y) in enumerate(all_data):
        row = i // cols + 1
        col = i % cols + 1
        
        plt.subplot(row, col)
        
        if x_labels and y:
            x_indices = list(range(len(x_labels)))
            color = CHART_COLORS[i % len(CHART_COLORS)]
            plt.plot(x_indices, y, marker="dot", color=color)
            
            # Set x-axis labels (fewer labels for subplots)
            num_labels = min(5, len(x_labels))
            if len(x_labels) > num_labels:
                step = len(x_labels) // num_labels
                label_indices = list(range(0, len(x_labels), step))
                label_values = [x_labels[i] for i in label_indices]
            else:
                label_indices = x_indices
                label_values = x_labels
            
            plt.xticks(label_indices, label_values)
        else:
            # Empty plot with message
            plt.plot([0], [0])
        
        # Shorter title for subplots
        plt.title(metric_class.title[:40] + "..." if len(metric_class.title) > 40 else metric_class.title)
        plt.ylabel(metric_class.unit)
        plt.grid(True, True)
    
    plt.show()


def print_examples():
    """Print usage examples."""
    print("\nExamples:")
    print("  # Show last 60 minutes (default)")
    print("  python dashboard.py ingress-rps-total")
    print("")
    print("  # Use a different Prometheus server")
    print("  python dashboard.py ingress-rps-total --url http://prometheus.example.com:9090")
    print("")
    print("  # Show last 120 minutes")
    print("  python dashboard.py ingress-rps-total -m 120")
    print("")
    print("  # Show specific time range on November 13th, 8:00 to 10:00 AM")
    print('  python dashboard.py ingress-error-rate --from "Nov 13 08:00" --to "Nov 13 10:00"')
    print("")
    print("  # Using different date formats")
    print('  python dashboard.py haproxy-cpu --from "2024-11-13 08:00" --to "2024-11-13 10:00"')
    print('  python dashboard.py haproxy-cpu --from "11-13 08:00" --to "11-13 10:00"')
    print("")
    print("  # From a specific time until now")
    print('  python dashboard.py ingress-latency-p99 --from "Nov 13 08:00"')
    print("")
    print("  # List all available metrics")
    print("  python dashboard.py --list")


def print_metrics_list(metrics_dict, category_filter=None):
    """Print available metrics organized by category."""
    
    # Organize metrics by category
    categories = {
        "General System": [],
        # Ingress-perf categories
        "Ingress RPS (Requests/sec)": [],
        "Ingress Latency": [],
        "HAProxy": [],
        "Infrastructure Nodes": [],
        "Ingress Connections": [],
        "Ingress Error/Quality": [],
        "Ingress Throughput": [],
        "Router": [],
        # k8s-netperf categories
        "Node Network Throughput": [],
        "Pod Network Throughput": [],
        "TCP Metrics": [],
        "UDP Metrics": [],
        "Network Errors/Drops": [],
        "Socket Statistics": [],
        "Container Network I/O": [],
        "Network Interface": [],
        "Conntrack": [],
        # kube-burner categories
        "Cluster Status": [],
        "Node/Pod Status": [],
        "Kube API Server": [],
        "Controller & Scheduler": [],
        "Kubelet & CRI-O": [],
        "Pod Latency": [],
        "Services & Kubeproxy": [],
        "Alerts": [],
        "Workload Resources": [],
        # etcd-on-cluster categories
        "Etcd Detailed": [],
        # OVN categories
        "OVN Components": [],
        "OVN Network": [],
        # OCP Performance categories
        "Cluster Overview": [],
        "Container Resources": [],
        "API Performance": [],
        # HyperShift categories
        "HyperShift": [],
    }
    
    # Categorize each metric
    for key, metric in metrics_dict.items():
        title = metric.title.lower()
        # Ingress-perf metrics
        if "ingress rps" in title or key.startswith("ingress-rps"):
            categories["Ingress RPS (Requests/sec)"].append((key, metric))
        elif "ingress" in title and "latency" in title:
            categories["Ingress Latency"].append((key, metric))
        elif "haproxy" in title:
            categories["HAProxy"].append((key, metric))
        elif key.startswith("infra-"):
            categories["Infrastructure Nodes"].append((key, metric))
        elif "ingress" in title and "connection" in title:
            categories["Ingress Connections"].append((key, metric))
        elif "ingress" in title and ("error" in title or "success" in title or "backend" in title):
            categories["Ingress Error/Quality"].append((key, metric))
        elif "ingress" in title and "bytes" in title:
            categories["Ingress Throughput"].append((key, metric))
        elif "router" in title:
            categories["Router"].append((key, metric))
        # k8s-netperf metrics
        elif key.startswith("node-net"):
            categories["Node Network Throughput"].append((key, metric))
        elif key.startswith("pod-net"):
            categories["Pod Network Throughput"].append((key, metric))
        elif key.startswith("tcp-"):
            categories["TCP Metrics"].append((key, metric))
        elif key.startswith("udp-"):
            categories["UDP Metrics"].append((key, metric))
        elif "drop" in title or (key.startswith("net-error")):
            categories["Network Errors/Drops"].append((key, metric))
        elif "socket" in title:
            categories["Socket Statistics"].append((key, metric))
        elif key.startswith("container-net"):
            categories["Container Network I/O"].append((key, metric))
        elif key.startswith("net-interface") or key.startswith("net-packets"):
            categories["Network Interface"].append((key, metric))
        elif "conntrack" in title:
            categories["Conntrack"].append((key, metric))
        # kube-burner metrics
        elif key.startswith("masters-") or key.startswith("workers-"):
            categories["Cluster Status"].append((key, metric))
        elif key.startswith("nodes-") or key.startswith("pod-count") or key.startswith("pods-"):
            categories["Node/Pod Status"].append((key, metric))
        elif key.startswith("kube-api"):
            categories["Kube API Server"].append((key, metric))
        elif key.startswith("kube-controller") or key.startswith("kube-scheduler") or key.startswith("scheduling"):
            categories["Controller & Scheduler"].append((key, metric))
        elif key.startswith("kubelet-") or key.startswith("crio-"):
            categories["Kubelet & CRI-O"].append((key, metric))
        elif key.startswith("pod-ready") or key.startswith("container-start"):
            categories["Pod Latency"].append((key, metric))
        elif key.startswith("service-") or key.startswith("endpoints") or key.startswith("services-"):
            categories["Services & Kubeproxy"].append((key, metric))
        elif "alert" in title:
            categories["Alerts"].append((key, metric))
        elif key.startswith("deployments") or key.startswith("replicasets") or key.startswith("namespaces") or key.startswith("secrets") or key.startswith("configmaps"):
            categories["Workload Resources"].append((key, metric))
        # etcd detailed metrics
        elif key.startswith("etcd-"):
            categories["Etcd Detailed"].append((key, metric))
        # OVN metrics
        elif key.startswith("ovn-") and ("cpu" in title or "memory" in title):
            categories["OVN Components"].append((key, metric))
        elif key.startswith("ovn-"):
            categories["OVN Network"].append((key, metric))
        # OCP Performance metrics
        elif key.startswith("cluster-"):
            categories["Cluster Overview"].append((key, metric))
        elif key.startswith("container-") or key.startswith("api-"):
            categories["Container Resources"].append((key, metric))
        elif key.startswith("api-"):
            categories["API Performance"].append((key, metric))
        # HyperShift metrics
        elif key.startswith("hosted-") or key.startswith("management-") or key.startswith("control-plane") or key.startswith("hypershift-"):
            categories["HyperShift"].append((key, metric))
        # Node count (separate from node-net)
        elif key.startswith("node-count"):
            categories["Node/Pod Status"].append((key, metric))
        else:
            categories["General System"].append((key, metric))
    
    # Print organized list
    print("\n" + "=" * 60)
    print(" AVAILABLE METRICS")
    print("=" * 60)
    
    for category, metrics_list in categories.items():
        if not metrics_list:
            continue
        if category_filter and category_filter.lower() not in category.lower():
            continue
            
        print(f"\n┌─ {category}")
        print("│")
        for key, metric in metrics_list:
            print(f"│  {key:25} → {metric.title}")
        print("│")
    
    print("\n" + "=" * 60)
    print(f" Total: {len(metrics_dict)} metrics available")
    print("=" * 60 + "\n")


# ==========================================================================
# METRICS REGISTRY
# Mapping of command-line keywords to metric classes
# ==========================================================================

AVAILABLE_METRICS = {
    # ==========================================================================
    # INGRESS-PERF METRICS (from ingress-perf.jsonnet)
    # ==========================================================================
    
    # ── Ingress RPS Metrics ───────────────────────────────────────────────
    "ingress-rps-edge": my_metrics.IngressRPSEdgeMetric,
    "ingress-rps-passthrough": my_metrics.IngressRPSPassthroughMetric,
    "ingress-rps-reencrypt": my_metrics.IngressRPSReencryptMetric,
    "ingress-rps-http": my_metrics.IngressRPSHttpMetric,
    "ingress-rps-total": my_metrics.IngressRPSTotalMetric,
    
    # ── Ingress Latency Metrics ───────────────────────────────────────────
    "ingress-latency-avg": my_metrics.IngressLatencyAvgMetric,
    "ingress-latency-p99": my_metrics.IngressLatencyP99Metric,
    "ingress-latency-p90": my_metrics.IngressLatencyP90Metric,
    "ingress-latency-p50": my_metrics.IngressLatencyP50Metric,
    
    # ── HAProxy CPU Metrics ───────────────────────────────────────────────
    "haproxy-cpu": my_metrics.HAProxyCPUAvgMetric,
    "haproxy-cpu-max": my_metrics.HAProxyCPUMaxMetric,
    
    # ── Infrastructure Nodes CPU ──────────────────────────────────────────
    "infra-cpu": my_metrics.InfraNodesCPUAvgMetric,
    "infra-cpu-max": my_metrics.InfraNodesCPUMaxMetric,
    
    # ── Ingress Connection Metrics ────────────────────────────────────────
    "ingress-connections": my_metrics.IngressActiveConnectionsMetric,
    "ingress-conn-rate": my_metrics.IngressConnectionRateMetric,
    
    # ── Ingress Error and Quality Metrics ─────────────────────────────────
    "ingress-error-rate": my_metrics.IngressErrorRateMetric,
    "ingress-success-rate": my_metrics.IngressSuccessRateMetric,
    "ingress-backends-down": my_metrics.IngressBackendDownMetric,
    
    # ── Ingress Throughput Metrics ────────────────────────────────────────
    "ingress-bytes-in": my_metrics.IngressBytesInMetric,
    "ingress-bytes-out": my_metrics.IngressBytesOutMetric,
    
    # ── Router Metrics ────────────────────────────────────────────────────
    "router-reload": my_metrics.RouterReloadMetric,
    "router-config-time": my_metrics.RouterWriteConfigMetric,
    
    # ==========================================================================
    # K8S-NETPERF METRICS (from k8s-netperf.jsonnet)
    # ==========================================================================
    
    # ── Node Network Throughput (Node to Node) ────────────────────────────
    "node-net-tx": my_metrics.NodeNetworkThroughputTxMetric,
    "node-net-rx": my_metrics.NodeNetworkThroughputRxMetric,
    "node-net-total": my_metrics.NodeNetworkThroughputTotalMetric,
    
    # ── Pod Network Throughput (Pod to Pod) ───────────────────────────────
    "pod-net-tx": my_metrics.PodNetworkThroughputTxMetric,
    "pod-net-rx": my_metrics.PodNetworkThroughputRxMetric,
    "pod-net-total": my_metrics.PodNetworkThroughputTotalMetric,
    
    # ── TCP Metrics ───────────────────────────────────────────────────────
    "tcp-established": my_metrics.TCPConnectionsEstablishedMetric,
    "tcp-active-opens": my_metrics.TCPConnectionsActiveMetric,
    "tcp-passive-opens": my_metrics.TCPConnectionsPassiveMetric,
    "tcp-retransmits": my_metrics.TCPRetransmitsMetric,
    "tcp-segments-tx": my_metrics.TCPSegmentsTxMetric,
    "tcp-segments-rx": my_metrics.TCPSegmentsRxMetric,
    
    # ── UDP Metrics ───────────────────────────────────────────────────────
    "udp-tx": my_metrics.UDPPacketsTxMetric,
    "udp-rx": my_metrics.UDPPacketsRxMetric,
    "udp-errors": my_metrics.UDPErrorsMetric,
    
    # ── Network Errors and Drops ──────────────────────────────────────────
    "net-drops-tx": my_metrics.NetworkPacketDropsTxMetric,
    "net-drops-rx": my_metrics.NetworkPacketDropsRxMetric,
    "net-errors-tx": my_metrics.NetworkErrorsTxMetric,
    "net-errors-rx": my_metrics.NetworkErrorsRxMetric,
    
    # ── Socket Statistics ─────────────────────────────────────────────────
    "socket-timewait": my_metrics.SocketTimeWaitMetric,
    "socket-allocated": my_metrics.SocketAllocatedMetric,
    "socket-inuse": my_metrics.SocketInUseMetric,
    
    # ── Container Network I/O ─────────────────────────────────────────────
    "container-net-tx-ns": my_metrics.ContainerNetworkTxByNamespaceMetric,
    "container-net-rx-ns": my_metrics.ContainerNetworkRxByNamespaceMetric,
    
    # ── Network Interface Statistics ──────────────────────────────────────
    "net-interface-speed": my_metrics.NetworkInterfaceSpeedMetric,
    "net-packets-tx": my_metrics.NetworkPacketsTxMetric,
    "net-packets-rx": my_metrics.NetworkPacketsRxMetric,
    
    # ── Conntrack ─────────────────────────────────────────────────────────
    "conntrack-entries": my_metrics.ConntrackEntriesMetric,
    "conntrack-usage": my_metrics.ConntrackUsageMetric,
    
    # ==========================================================================
    # KUBE-BURNER METRICS (from kube-burner-report-ocp-wrapper.jsonnet)
    # ==========================================================================
    
    # ── Cluster Status (Masters/Workers) ────────────────────────────────────
    "masters-cpu": my_metrics.MastersCPUUtilizationMetric,
    "masters-memory": my_metrics.MastersMemoryUtilizationMetric,
    "workers-cpu": my_metrics.WorkersCPUUtilizationMetric,
    "workers-memory": my_metrics.WorkersMemoryUtilizationMetric,
    
    # ── Node and Pod Status ─────────────────────────────────────────────────
    "node-count": my_metrics.NodeCountMetric,
    "nodes-ready": my_metrics.NodeReadyCountMetric,
    "nodes-notready": my_metrics.NodeNotReadyCountMetric,
    "pod-count": my_metrics.PodCountMetric,
    "pods-running": my_metrics.PodRunningCountMetric,
    "pods-pending": my_metrics.PodPendingCountMetric,
    "pods-failed": my_metrics.PodFailedCountMetric,
    
    # ── Kube API Server ─────────────────────────────────────────────────────
    "kube-api-cpu": my_metrics.KubeAPIServerCPUMetric,
    "kube-api-memory": my_metrics.KubeAPIServerMemoryMetric,
    "kube-api-request-rate": my_metrics.KubeAPIRequestRateMetric,
    "kube-api-latency-p99": my_metrics.KubeAPIRequestLatencyP99Metric,
    "kube-api-latency-p50": my_metrics.KubeAPIRequestLatencyP50Metric,
    
    # ── Controller Manager and Scheduler ────────────────────────────────────
    "kube-controller-cpu": my_metrics.KubeControllerManagerCPUMetric,
    "kube-controller-memory": my_metrics.KubeControllerManagerMemoryMetric,
    "kube-scheduler-cpu": my_metrics.KubeSchedulerCPUMetric,
    "kube-scheduler-memory": my_metrics.KubeSchedulerMemoryMetric,
    "scheduling-throughput": my_metrics.SchedulingThroughputMetric,
    
    # ── Etcd ────────────────────────────────────────────────────────────────
    "etcd-leader-changes": my_metrics.EtcdLeaderChangesMetric,
    "etcd-db-size": my_metrics.EtcdDBSizeMetric,
    "etcd-peer-rtt-p99": my_metrics.EtcdPeerRTTP99Metric,
    "etcd-wal-sync-p99": my_metrics.EtcdWALSyncDurationP99Metric,
    "etcd-backend-commit-p99": my_metrics.EtcdBackendCommitDurationP99Metric,
    "etcd-cpu": my_metrics.EtcdCPUMetric,
    "etcd-memory": my_metrics.EtcdMemoryMetric,
    
    # ── OVN-Kubernetes ──────────────────────────────────────────────────────
    "ovn-master-cpu": my_metrics.OVNKubeMasterCPUMetric,
    "ovn-master-memory": my_metrics.OVNKubeMasterMemoryMetric,
    "ovn-node-cpu": my_metrics.OVNKubeNodeCPUMetric,
    "ovn-node-memory": my_metrics.OVNKubeNodeMemoryMetric,
    "ovn-controller-cpu": my_metrics.OVNControllerCPUMetric,
    
    # ── Kubelet and CRI-O ───────────────────────────────────────────────────
    "kubelet-cpu": my_metrics.KubeletCPUMetric,
    "kubelet-memory": my_metrics.KubeletMemoryMetric,
    "crio-cpu": my_metrics.CRIOCPUMetric,
    "crio-memory": my_metrics.CRIOMemoryMetric,
    
    # ── Pod Latency ─────────────────────────────────────────────────────────
    "pod-ready-latency-p99": my_metrics.PodReadyLatencyP99Metric,
    "pod-ready-latency-p50": my_metrics.PodReadyLatencyP50Metric,
    "container-start-latency-p99": my_metrics.ContainerStartLatencyP99Metric,
    
    # ── Services and Kubeproxy ──────────────────────────────────────────────
    "service-sync-latency-p99": my_metrics.ServiceSyncLatencyP99Metric,
    "endpoints-count": my_metrics.EndpointsCountMetric,
    "services-count": my_metrics.ServicesCountMetric,
    
    # ── Alerts ──────────────────────────────────────────────────────────────
    "alerts-firing": my_metrics.AlertsFiringCountMetric,
    "alerts-pending": my_metrics.AlertsPendingCountMetric,
    
    # ── Workload Resources ──────────────────────────────────────────────────
    "deployments-count": my_metrics.DeploymentsCountMetric,
    "replicasets-count": my_metrics.ReplicaSetsCountMetric,
    "namespaces-count": my_metrics.NamespacesCountMetric,
    "secrets-count": my_metrics.SecretsCountMetric,
    "configmaps-count": my_metrics.ConfigMapsCountMetric,
    
    # ==========================================================================
    # ETCD DETAILED METRICS (from etcd-on-cluster-dashboard.jsonnet)
    # ==========================================================================
    
    # ── Etcd Disk I/O ─────────────────────────────────────────────────────────
    "etcd-disk-writes": my_metrics.EtcdDiskWritesMetric,
    "etcd-disk-reads": my_metrics.EtcdDiskReadsMetric,
    
    # ── Etcd Compaction/Defrag ────────────────────────────────────────────────
    "etcd-compaction-duration": my_metrics.EtcdCompactionDurationMetric,
    "etcd-defrag-duration": my_metrics.EtcdDefragDurationMetric,
    
    # ── Etcd DB Space ─────────────────────────────────────────────────────────
    "etcd-db-space-used": my_metrics.EtcdDBSpaceUsedPercentMetric,
    "etcd-db-left-capacity": my_metrics.EtcdDBLeftCapacityMetric,
    "etcd-db-size-limit": my_metrics.EtcdDBSizeLimitMetric,
    
    # ── Etcd Keys/Operations ──────────────────────────────────────────────────
    "etcd-keys": my_metrics.EtcdKeysCountMetric,
    "etcd-slow-ops": my_metrics.EtcdSlowOperationsMetric,
    "etcd-key-ops": my_metrics.EtcdKeyOperationsMetric,
    "etcd-compacted-keys": my_metrics.EtcdCompactedKeysMetric,
    
    # ── Etcd Raft/Leader ──────────────────────────────────────────────────────
    "etcd-raft-proposals": my_metrics.EtcdRaftProposalsMetric,
    "etcd-failed-proposals": my_metrics.EtcdFailedProposalsMetric,
    "etcd-heartbeat-failures": my_metrics.EtcdHeartbeatFailuresMetric,
    "etcd-has-leader": my_metrics.EtcdHasLeaderMetric,
    
    # ── Etcd Network ──────────────────────────────────────────────────────────
    "etcd-net-tx": my_metrics.EtcdNetworkTrafficTxMetric,
    "etcd-net-rx": my_metrics.EtcdNetworkTrafficRxMetric,
    "etcd-grpc-traffic": my_metrics.EtcdGRPCTrafficMetric,
    "etcd-active-streams": my_metrics.EtcdActiveStreamsMetric,
    "etcd-snapshot-duration": my_metrics.EtcdSnapshotDurationMetric,
    
    # ==========================================================================
    # OCP PERFORMANCE METRICS (from ocp-performance.jsonnet)
    # ==========================================================================
    
    # ── Cluster Overview ──────────────────────────────────────────────────────
    "cluster-cpu": my_metrics.ClusterCPUUsageMetric,
    "cluster-memory": my_metrics.ClusterMemoryUsageMetric,
    "cluster-memory-total": my_metrics.ClusterMemoryTotalMetric,
    "cluster-filesystem": my_metrics.ClusterFilesystemUsageMetric,
    
    # ── Container Resources ───────────────────────────────────────────────────
    "container-cpu-top": my_metrics.ContainerCPUUsageTopMetric,
    "container-memory-top": my_metrics.ContainerMemoryUsageTopMetric,
    "container-restarts": my_metrics.ContainerRestartsTotalMetric,
    "container-oom-kills": my_metrics.ContainerOOMKillsMetric,
    
    # ── API Performance ───────────────────────────────────────────────────────
    "api-request-duration": my_metrics.APIServerRequestDurationAvgMetric,
    "api-error-rate": my_metrics.APIServerRequestErrorRateMetric,
    "api-inflight-requests": my_metrics.APIServerInFlightRequestsMetric,
    
    # ==========================================================================
    # OVN METRICS (from ovn-dashboard.jsonnet)
    # ==========================================================================
    
    # ── OVN Components ────────────────────────────────────────────────────────
    "ovn-controller-memory": my_metrics.OVNControllerMemoryMetric,
    "ovn-northd-cpu": my_metrics.OVNNorthdCPUMetric,
    "ovn-northd-memory": my_metrics.OVNNorthdMemoryMetric,
    "ovn-nbdb-cpu": my_metrics.OVNNbdbCPUMetric,
    "ovn-nbdb-memory": my_metrics.OVNNbdbMemoryMetric,
    "ovn-sbdb-cpu": my_metrics.OVNSbdbCPUMetric,
    "ovn-sbdb-memory": my_metrics.OVNSbdbMemoryMetric,
    
    # ── OVN Flows/Network ─────────────────────────────────────────────────────
    "ovn-flow-count": my_metrics.OVNFlowCountMetric,
    "ovn-flow-add-rate": my_metrics.OVNFlowAddRateMetric,
    "ovn-pod-latency-p99": my_metrics.OVNPodCreationLatencyP99Metric,
    "ovn-pod-latency-p50": my_metrics.OVNPodCreationLatencyP50Metric,
    
    # ==========================================================================
    # HYPERSHIFT METRICS (from hypershift-performance.jsonnet)
    # ==========================================================================
    
    # ── Hosted Clusters ───────────────────────────────────────────────────────
    "hosted-cluster-count": my_metrics.HostedClusterCountMetric,
    "hosted-clusters-available": my_metrics.HostedClusterAvailableMetric,
    
    # ── Management Cluster ────────────────────────────────────────────────────
    "management-cluster-cpu": my_metrics.ManagementClusterCPUMetric,
    "management-cluster-memory": my_metrics.ManagementClusterMemoryMetric,
    
    # ── Control Plane ─────────────────────────────────────────────────────────
    "control-plane-cpu": my_metrics.ControlPlaneCPUTotalMetric,
    "control-plane-memory": my_metrics.ControlPlaneMemoryTotalMetric,
    "hypershift-operator-cpu": my_metrics.HyperShiftOperatorCPUMetric,
    "hypershift-operator-memory": my_metrics.HyperShiftOperatorMemoryMetric,
}


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description='DotMatrixPrometheus - Terminal-based Prometheus metrics visualization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Single metric - last 60 minutes (default)
  %(prog)s ingress-rps-total

  # Multiple metrics in grid layout
  %(prog)s cluster-cpu cluster-memory etcd-cpu etcd-memory

  # Multiple metrics with custom columns
  %(prog)s masters-cpu workers-cpu etcd-cpu --cols 3

  # With time range
  %(prog)s cluster-cpu etcd-db-size --from "Nov 13 08:00" --to "Nov 13 10:00"

  # Last 120 minutes
  %(prog)s ingress-rps-total -m 120

  # From a specific time until now
  %(prog)s ingress-latency-p99 --from "Nov 13 08:00"

Supported datetime formats:
  - "2024-11-13 08:00" or "2024-11-13T08:00"
  - "11-13 08:00" or "11/13 08:00"
  - "Nov 13 08:00" or "November 13 08:00"
  - "08:00" (uses today's date)
'''
    )
    
    parser.add_argument(
        'metrics',
        nargs='*',
        help='Metric name(s) to plot. Multiple metrics will be shown in a grid (use --list to see available metrics)'
    )
    
    parser.add_argument(
        '--url', '-u',
        dest='prometheus_url',
        default=DEFAULT_PROMETHEUS_URL,
        metavar='URL',
        help=f'Prometheus server URL (default: {DEFAULT_PROMETHEUS_URL})'
    )
    
    parser.add_argument(
        '--from', '-f',
        dest='start_time',
        metavar='DATETIME',
        help='Start datetime (e.g., "Nov 13 08:00", "2024-11-13 08:00")'
    )
    
    parser.add_argument(
        '--to', '-t',
        dest='end_time',
        metavar='DATETIME',
        help='End datetime (e.g., "Nov 13 10:00", "10:00")'
    )
    
    parser.add_argument(
        '--minutes', '-m',
        type=int,
        default=60,
        help='Minutes to look back from now (default: 60, ignored if --from/--to provided)'
    )
    
    parser.add_argument(
        '--cols', '-c',
        type=int,
        default=None,
        help='Number of columns for multi-metric grid layout (default: auto)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available metrics'
    )
    
    parser.add_argument(
        '--list-ingress', '-li',
        action='store_true',
        help='List only ingress-perf metrics'
    )
    
    parser.add_argument(
        '--list-netperf', '-ln',
        action='store_true',
        help='List only k8s-netperf metrics'
    )
    
    parser.add_argument(
        '--list-kubeburner', '-lk',
        action='store_true',
        help='List only kube-burner metrics'
    )
    
    parser.add_argument(
        '--list-etcd', '-le',
        action='store_true',
        help='List only etcd metrics'
    )
    
    parser.add_argument(
        '--list-ovn', '-lo',
        action='store_true',
        help='List only OVN metrics'
    )
    
    parser.add_argument(
        '--list-ocp', '-lp',
        action='store_true',
        help='List only OCP performance metrics'
    )
    
    parser.add_argument(
        '--list-hypershift', '-lh',
        action='store_true',
        help='List only HyperShift metrics'
    )
    
    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    
    # ==========================================================================
    # COMMAND LINE HANDLING
    # ==========================================================================
    
    # Handle --list
    if args.list:
        print_metrics_list(AVAILABLE_METRICS)
        sys.exit(0)
    
    # Handle --list-ingress
    if args.list_ingress:
        ingress_metrics = {k: v for k, v in AVAILABLE_METRICS.items() 
                          if k.startswith("ingress-") or k.startswith("haproxy-") 
                          or k.startswith("infra-") or k.startswith("router-")}
        print("\n🔥 INGRESS-PERF METRICS")
        print("Based on: cloud-bulldozer/performance-dashboards ingress-perf.jsonnet\n")
        print_metrics_list(ingress_metrics)
        sys.exit(0)
    
    # Handle --list-netperf
    if args.list_netperf:
        netperf_metrics = {k: v for k, v in AVAILABLE_METRICS.items() 
                          if k.startswith("node-net") or k.startswith("pod-net")
                          or k.startswith("tcp-") or k.startswith("udp-")
                          or k.startswith("net-") or k.startswith("socket-")
                          or k.startswith("container-net") or k.startswith("conntrack-")}
        print("\n🌐 K8S-NETPERF METRICS")
        print("Based on: cloud-bulldozer/performance-dashboards k8s-netperf.jsonnet\n")
        print_metrics_list(netperf_metrics)
        sys.exit(0)
    
    # Handle --list-kubeburner
    if args.list_kubeburner:
        kubeburner_metrics = {k: v for k, v in AVAILABLE_METRICS.items() 
                             if k.startswith("masters-") or k.startswith("workers-")
                             or k.startswith("pods-") or k.startswith("nodes-")
                             or k.startswith("kube-api") or k.startswith("kube-controller")
                             or k.startswith("kube-scheduler") or k.startswith("scheduling")
                             or k.startswith("kubelet-") or k.startswith("crio-")
                             or k.startswith("pod-ready") or k.startswith("container-start")
                             or k.startswith("service-") or k.startswith("endpoints")
                             or k.startswith("services-") or k.startswith("alerts-")
                             or k.startswith("deployments") or k.startswith("replicasets")
                             or k.startswith("namespaces") or k.startswith("secrets")
                             or k.startswith("configmaps") or k == "node-count" or k == "pod-count"}
        print("\n🔥 KUBE-BURNER METRICS")
        print("Based on: cloud-bulldozer/performance-dashboards kube-burner-report-ocp-wrapper.jsonnet\n")
        print_metrics_list(kubeburner_metrics)
        sys.exit(0)
    
    # Handle --list-etcd
    if args.list_etcd:
        etcd_metrics = {k: v for k, v in AVAILABLE_METRICS.items() 
                        if k.startswith("etcd-")}
        print("\n💾 ETCD METRICS")
        print("Based on: cloud-bulldozer/performance-dashboards etcd-on-cluster-dashboard.jsonnet\n")
        print_metrics_list(etcd_metrics)
        sys.exit(0)
    
    # Handle --list-ovn
    if args.list_ovn:
        ovn_metrics = {k: v for k, v in AVAILABLE_METRICS.items() 
                       if k.startswith("ovn-")}
        print("\n🔌 OVN METRICS")
        print("Based on: cloud-bulldozer/performance-dashboards ovn-dashboard.jsonnet\n")
        print_metrics_list(ovn_metrics)
        sys.exit(0)
    
    # Handle --list-ocp
    if args.list_ocp:
        ocp_metrics = {k: v for k, v in AVAILABLE_METRICS.items() 
                       if k.startswith("cluster-") or k.startswith("container-")
                       or k.startswith("api-")}
        print("\n☸️  OCP PERFORMANCE METRICS")
        print("Based on: cloud-bulldozer/performance-dashboards ocp-performance.jsonnet\n")
        print_metrics_list(ocp_metrics)
        sys.exit(0)
    
    # Handle --list-hypershift
    if args.list_hypershift:
        hypershift_metrics = {k: v for k, v in AVAILABLE_METRICS.items() 
                              if k.startswith("hosted-") or k.startswith("management-")
                              or k.startswith("control-plane") or k.startswith("hypershift-")}
        print("\n🚀 HYPERSHIFT METRICS")
        print("Based on: cloud-bulldozer/performance-dashboards hypershift-performance.jsonnet\n")
        print_metrics_list(hypershift_metrics)
        sys.exit(0)
    
    # Require metric(s) if not listing
    if not args.metrics:
        print("Error: Please specify one or more metrics to plot.\n")
        print_examples()
        print("\nUse --list to see available metrics.")
        sys.exit(1)
    
    # Validate all metric selections
    invalid_metrics = []
    valid_metrics = []
    for metric_name in args.metrics:
        if metric_name not in AVAILABLE_METRICS:
            invalid_metrics.append(metric_name)
        else:
            valid_metrics.append(metric_name)
    
    if invalid_metrics:
        for metric_name in invalid_metrics:
            print(f"❌ Unknown metric: '{metric_name}'")
            suggestions = [k for k in AVAILABLE_METRICS.keys() if metric_name.lower() in k.lower()]
            if suggestions:
                print("   Did you mean one of these?")
                for s in suggestions[:3]:
                    print(f"   • {s}")
        print("\nUse --list to see all available metrics.")
        sys.exit(1)
    
    # Parse datetime arguments
    start_time = None
    end_time = None
    
    if args.start_time:
        try:
            start_time = parse_datetime(args.start_time)
        except ValueError as e:
            print(f"❌ Invalid --from datetime: {e}")
            sys.exit(1)
    
    if args.end_time:
        try:
            end_time = parse_datetime(args.end_time)
        except ValueError as e:
            print(f"❌ Invalid --to datetime: {e}")
            sys.exit(1)
    
    # Validate time range
    if start_time and end_time and start_time >= end_time:
        print(f"❌ Invalid time range: start ({start_time}) must be before end ({end_time})")
        sys.exit(1)
    
    # Draw the chart(s)
    try:
        if len(valid_metrics) == 1:
            # Single metric - use simple chart
            selected_metric = AVAILABLE_METRICS[valid_metrics[0]]
            draw_chart(
                selected_metric,
                prometheus_url=args.prometheus_url,
                minutes=args.minutes,
                start_time=start_time,
                end_time=end_time
            )
        else:
            # Multiple metrics - use grid layout
            metric_classes = [AVAILABLE_METRICS[m] for m in valid_metrics]
            draw_multi_chart(
                metric_classes,
                valid_metrics,
                prometheus_url=args.prometheus_url,
                minutes=args.minutes,
                start_time=start_time,
                end_time=end_time,
                cols=args.cols
            )
    except PrometheusConnectionError as e:
        print(f"❌ {e}")
        sys.exit(1)
