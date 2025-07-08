import requests
from typing import Optional, Dict, Any, Union
import json


class APIClient:
    """Python API client for https://api.example.com"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        """
        Initialize the API client
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for the API (default: https://api.example.com)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.exceptions.RequestException: For request errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return {'data': response.text}
                
        except requests.exceptions.RequestException as e:
            raise APIClientError(f"Request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make GET request
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data
        """
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make POST request
        
        Args:
            endpoint: API endpoint
            data: Request payload
            
        Returns:
            Response data
        """
        return self._make_request('POST', endpoint, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make PUT request
        
        Args:
            endpoint: API endpoint
            data: Request payload
            
        Returns:
            Response data
        """
        return self._make_request('PUT', endpoint, json=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make DELETE request
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Response data
        """
        return self._make_request('DELETE', endpoint)


class APIClientError(Exception):
    """Custom exception for API client errors"""
    pass


if __name__ == "__main__":
    # Example usage
    client = APIClient(api_key="your_api_key_here")
    
    try:
        # GET request example
        response = client.get("/users")
        print("GET /users:", response)
        
        # POST request example
        new_user = {"name": "John Doe", "email": "john@example.com"}
        response = client.post("/users", data=new_user)
        print("POST /users:", response)
        
        # PUT request example
        updated_user = {"name": "Jane Doe", "email": "jane@example.com"}
        response = client.put("/users/1", data=updated_user)
        print("PUT /users/1:", response)
        
        # DELETE request example
        response = client.delete("/users/1")
        print("DELETE /users/1:", response)
        
    except APIClientError as e:
        print(f"API Error: {e}")