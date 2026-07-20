# Load observability first so LANGSMITH_* OTel flags are set before langgraph imports.
from .observability import configure_observability, instrument_libraries

configure_observability()
instrument_libraries()
