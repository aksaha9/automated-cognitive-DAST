import os
import time
from zapv2 import ZAPv2
from app.models import ScanState, Vulnerability

class ZapService:
    def __init__(self):
        self.zap_url = os.getenv("ZAP_URL", "http://zap:8080")
        self.api_key = os.getenv("ZAP_API_KEY", "change-me-920394")
        self.zap = ZAPv2(apikey=self.api_key, proxies={'http': self.zap_url, 'https': self.zap_url})
    
    def start_spider(self, target_url: str) -> str:
        """Starts the spider scrape and returns scan ID"""
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
            
        print(f"Starting Spider for {target_url}")
        # ZAP returns the scan ID as a string, e.g., "0"
        scan_id = self.zap.spider.scan(target_url)
        if not scan_id.isdigit():
             raise Exception(f"Failed to start spider: {scan_id}")
             
        print(f"Spider started with ID: {scan_id}")
        return scan_id

    def get_spider_status(self, scan_id: str) -> int:
        try:
            status = self.zap.spider.status(scan_id)
            print(f"DEBUG: Spider scan_id={scan_id} status={status}")
            return int(status) if status.isdigit() else 0
        except Exception as e:
            print(f"Error getting spider status for {scan_id}: {e}")
            return 0 

    def start_active_scan(self, target_url: str) -> str:
        """Starts the active scan"""
        if not target_url.startswith("http"):
            target_url = "https://" + target_url

        print(f"Starting Active Scan for {target_url}")
        scan_id = self.zap.ascan.scan(target_url)
        if not scan_id.isdigit():
             raise Exception(f"Failed to start active scan: {scan_id}")

        print(f"Active Scan started with ID: {scan_id}")
        return scan_id

    def get_active_scan_status(self, scan_id: str) -> int:
        try:
            status = self.zap.ascan.status(scan_id)
            return int(status) if status.isdigit() else 0
        except Exception as e:
            print(f"Error getting active scan status for {scan_id}: {e}")
            return 0

    def get_alerts(self, target_url: str):
        # Allow retry or fallback
        try:
            return self.zap.core.alerts(baseurl=target_url)
        except:
            return []

    def stop_scan(self, spider_id: str = None, ascan_id: str = None):
        if spider_id:
            try:
                self.zap.spider.stop(spider_id)
            except: pass
        if ascan_id:
             try:
                self.zap.ascan.stop(ascan_id)
             except: pass


    def shutdown(self):
        self.zap.core.shutdown()
