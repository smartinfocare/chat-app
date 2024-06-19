import os

class Settings:
 
    SECRET_KEY: str = os.getenv("SECRET_KEY", "t#e5r4a1l-o_15l0ng_s3cr3t_k3y_r4nd0m_ch4r4ct3r5")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

settings = Settings()
