import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ROADSense"
    API_V1_STR: str = "/api"
    
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"
    
    # Data files
    M1_DATA_PATH: str = os.getenv(
    "M1_DATA_PATH",
    r"C:\Users\Subha\OneDrive\Desktop\roadsense-ai\data\processed\m1_output\prioritized_detections.csv"
)
    M2_DATA_PATH: str = os.getenv(
    "M2_DATA_PATH",
    r"C:\Users\Subha\OneDrive\Desktop\roadsense-ai\data\processed\m2_output\damage_instances.geojson"
)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
