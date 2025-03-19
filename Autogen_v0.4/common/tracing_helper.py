from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry import trace
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
import os

def get_trace_provider() -> trace.TracerProvider:
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)
    #tracer = trace.get_tracer(__name__)
#    This is the exporter that sends data to Application Insights
    exporter = AzureMonitorTraceExporter(
        
        connection_string=os.environ["AZURE_APP_INSIGHTS_CONNECTION_STRING"]
        
    )
    span_processor = BatchSpanProcessor(exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    return tracer_provider



