from configparser import ConfigParser

class Config:
    def __init__(self, file: str = "config.ini"):
        config = ConfigParser()
        config.read(file)

        self.database_url = config["database"]["url"]
        self.schema = config["database"].get("schema", "public")
        self.schema_cache_ttl = int(config["cache"].get("schema_ttl", 300))
        self.schema_limit = config["rate_limit"].get("schema_limit", "5/minute")
        self.query_limit = config["rate_limit"].get("query_limit", "10/minute")
        self.host = config["server"].get("host", "127.0.0.1")
        self.port = int(config["server"].get("port", 8080))
        self.log_level = config["server"].get("log_level", "INFO")