import requests
from typing import Optional

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def register(self, username: str, email: str, password: str) -> dict:
        r = requests.post(
            f"{self.base_url}/auth/register",
            json={"username": username, "email": email, "password": password},
            timeout=10,
        )
        return self._handle(r)

    def login(self, username_or_email: str, password: str) -> dict:
        r = requests.post(
            f"{self.base_url}/auth/login",
            json={"username_or_email": username_or_email, "password": password},
            timeout=10,
        )
        return self._handle(r)

    def search_travel(
        self,
        departure: str,
        destination: str,
        depart_date: str,
        return_date: str,
        budget: Optional[int] = None
    ) -> list:
        params = {
            "departure": departure,
            "destination": destination,
            "depart_date": depart_date,
            "return_date": return_date,
        }
        if budget is not None:
            params["budget"] = budget

        r = requests.get(
            f"{self.base_url}/travel/search",
            params=params,
            timeout=15,
        )
        return self._handle(r)

    def travel_details(self, offer_id: str) -> dict:
        r = requests.get(
            f"{self.base_url}/travel/details/{offer_id}",
            timeout=15,
        )
        return self._handle(r)

    def _handle(self, r: requests.Response) -> dict:
        try:
            data = r.json()
        except Exception:
            data = {"detail": r.text}

        if r.status_code >= 400:
            msg = data.get("detail", "Erreur API")
            raise RuntimeError(msg)
        return data

    def get_packages(
        self,
        departure: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None
    ) -> list:
        params = {
            "departure": departure,
            "destination": destination,
            "depart_date": depart_date,
        }
        if return_date:
            params["return_date"] = return_date

        r = requests.get(
            f"{self.base_url}/travel/packages",
            params=params,
            timeout=20,
        )
        return self._handle(r)

    def get_hotels(self, city_code: str) -> list:
        params = {"city_code": city_code}
        r = requests.get(
            f"{self.base_url}/travel/hotels",
            params=params,
            timeout=15,
        )
        return self._handle(r)
