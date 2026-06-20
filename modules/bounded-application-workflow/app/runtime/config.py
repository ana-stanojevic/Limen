from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    """Bounded, versioned configuration for one agent's runtime execution. """

    agent_name: str = Field(min_length=1)
    config_version: str = Field(default="v1", min_length=1)
    max_attempts: int = Field(default=1, ge=1, le=5)
