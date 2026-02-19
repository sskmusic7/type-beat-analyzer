"""
ACRCloud Console API client
Uses Personal Access Token to fetch project credentials for Identification API
"""
import requests
import logging
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ACRCloudConsoleAPI:
    """
    ACRCloud Console API client
    Uses Personal Access Token (JWT) to manage projects and get credentials
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Args:
            token: Personal Access Token (JWT) from ACRCloud console
        """
        self.token = token or os.getenv("ACRCLOUD_PERSONAL_ACCESS_TOKEN")
        # Console API base URLs - try different patterns
        # Based on console URL: console.acrcloud.com/avr?region=eu-west-1
        self.base_url = "https://console.acrcloud.com/avr/api/v1"
        self.alt_base_urls = [
            "https://console.acrcloud.com/api/v1",
            "https://api.console.acrcloud.com/v1",
            "https://console-api.acrcloud.com/v1",
            "https://eu-west-1.console.acrcloud.com/api/v1"
        ]
        
        if not self.token:
            logger.warning("ACRCloud Personal Access Token not set")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"  # Some APIs expect this
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make API request with error handling"""
        if not self.token:
            logger.error("No Personal Access Token available")
            return None
        
        # Try main base URL first
        urls_to_try = [self.base_url] + self.alt_base_urls
        
        for base_url in urls_to_try:
            try:
                url = f"{base_url}{endpoint}"
                headers = self._get_headers()
                headers.update(kwargs.pop('headers', {}))
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=10,
                    **kwargs
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error(f"Authentication failed: {response.text}")
                    return None
                elif response.status_code == 404:
                    # Try next URL
                    continue
                else:
                    logger.warning(f"Request failed with status {response.status_code}: {response.text}")
                    # Return response anyway, might have useful error info
                    try:
                        return response.json()
                    except:
                        return {"error": response.text, "status_code": response.status_code}
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request to {base_url} failed: {e}")
                continue
        
        return None
    
    def list_base_projects(self) -> List[Dict]:
        """
        List all Base Projects (AVR type projects)
        
        Returns:
            List of project dictionaries
        """
        # Try different endpoint variations
        endpoints = [
            "/base-projects",
            "/projects",
            "/base-projects/list",
            "/projects/base",
            "/avr/projects"
        ]
        
        for endpoint in endpoints:
            result = self._make_request("GET", endpoint)
            if result and not result.get("error"):
                # Handle different response formats
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    if "data" in result:
                        return result["data"]
                    elif "projects" in result:
                        return result["projects"]
                    elif "items" in result:
                        return result["items"]
                    # If it's a single project, wrap it
                    elif "id" in result or "project_id" in result:
                        return [result]
        
        logger.warning("Could not list projects - endpoint not found")
        return []
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """
        Get details of a specific project
        
        Args:
            project_id: Project ID
            
        Returns:
            Project details including access_key and access_secret
        """
        endpoints = [
            f"/base-projects/{project_id}",
            f"/projects/{project_id}",
            f"/base-projects/{project_id}/details",
            f"/projects/{project_id}/credentials"
        ]
        
        for endpoint in endpoints:
            result = self._make_request("GET", endpoint)
            if result and not result.get("error"):
                return result
        
        return None
    
    def get_project_credentials(self, project_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get access_key and access_secret for a project
        
        Args:
            project_id: Optional project ID. If None, uses first available project.
            
        Returns:
            Dict with 'access_key', 'access_secret', and 'host'
        """
        # If no project_id, get first project
        if not project_id:
            projects = self.list_base_projects()
            if not projects:
                logger.error("No projects found. Create a Base Project (AVR type) in the console.")
                return None
            
            # Use first project
            project = projects[0]
            project_id = project.get("id") or project.get("project_id") or project.get("_id")
            
            if not project_id:
                logger.error("Could not extract project ID from project data")
                return None
        
        # Get project details
        project_details = self.get_project(project_id)
        if not project_details:
            logger.error(f"Could not fetch details for project {project_id}")
            return None
        
        # Extract credentials - they might be in different places
        access_key = (
            project_details.get("access_key") or
            project_details.get("accessKey") or
            project_details.get("api_key") or
            project_details.get("apiKey")
        )
        
        access_secret = (
            project_details.get("access_secret") or
            project_details.get("accessSecret") or
            project_details.get("api_secret") or
            project_details.get("apiSecret") or
            project_details.get("secret")
        )
        
        # Get host/region
        host = (
            project_details.get("host") or
            project_details.get("endpoint") or
            project_details.get("region")
        )
        
        # Determine host from region if needed
        if not host or not host.startswith("identify-"):
            region = project_details.get("region", "eu-west-1")
            if isinstance(region, dict):
                region = region.get("code", "eu-west-1")
            host = f"identify-{region}.acrcloud.com"
        
        if not access_key or not access_secret:
            logger.error("Project credentials not found in project details")
            logger.debug(f"Project details keys: {list(project_details.keys())}")
            return None
        
        return {
            "access_key": access_key,
            "access_secret": access_secret,
            "host": host,
            "project_id": project_id
        }
    
    def auto_configure(self) -> bool:
        """
        Automatically fetch and configure project credentials
        
        Returns:
            True if successful, False otherwise
        """
        credentials = self.get_project_credentials()
        if not credentials:
            return False
        
        # Update environment (in memory for this session)
        os.environ["ACRCLOUD_ACCESS_KEY"] = credentials["access_key"]
        os.environ["ACRCLOUD_ACCESS_SECRET"] = credentials["access_secret"]
        os.environ["ACRCLOUD_HOST"] = credentials["host"]
        
        logger.info(f"✅ Auto-configured ACRCloud credentials from project {credentials['project_id']}")
        logger.info(f"   Host: {credentials['host']}")
        
        return True
