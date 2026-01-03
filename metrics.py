# metrics.py
from prometheus_client import start_http_server, Gauge, Histogram, REGISTRY
import threading


class PrometheusMetrics:
    def __init__(self, port: int = 8000):
        self.port = port
        self.metrics = {}
        self._start_server()

    def _start_server(self):
        threading.Thread(target=start_http_server, args=(
            self.port,), daemon=True).start()
        print(
            f"Servidor Prometheus iniciado em http://localhost:{self.port}/metrics")

    def _get_existing_metric(self, name):
        """Busca métrica existente no registry global de forma segura."""
        for collector in REGISTRY._names_to_collectors.values():
            # Alguns coletores (ex.: GCCollector) não têm ._name, então usamos getattr
            collector_name = getattr(collector, "_name", None)
            if collector_name == name:
                return collector
        return None

    # ================= Gauge =================
    def create_gauge(self, name: str, description: str, labels: list = None):
        if name in self.metrics:
            return self.metrics[name]

        existing = self._get_existing_metric(name)
        if existing:
            self.metrics[name] = existing
            return existing

        if labels:
            gauge = Gauge(name, description, labels)
        else:
            gauge = Gauge(name, description)
        self.metrics[name] = gauge
        return gauge

    def set_gauge(self, name: str, value, label_values: dict = None):
        gauge = self.metrics.get(name)
        if gauge is None:
            raise ValueError(f"Métrica '{name}' não encontrada.")
        if label_values:
            gauge.labels(**label_values).set(value)
        else:
            gauge.set(value)

    # ================= Histogram =================
    def create_histogram(self, name: str, description: str, labels: list = None, buckets=None):
        if name in self.metrics:
            return self.metrics[name]

        existing = self._get_existing_metric(name)
        if existing:
            self.metrics[name] = existing
            return existing

        if labels:
            if buckets:
                hist = Histogram(name, description, labels, buckets=buckets)
            else:
                hist = Histogram(name, description, labels)
        else:
            hist = Histogram(name, description, buckets=buckets)
        self.metrics[name] = hist
        return hist

    def observe_histogram(self, name: str, value, label_values: dict = None):
        hist = self.metrics.get(name)
        if hist is None:
            raise ValueError(f"Métrica '{name}' não encontrada.")
        if label_values:
            hist.labels(**label_values).observe(value)
        else:
            hist.observe(value)
