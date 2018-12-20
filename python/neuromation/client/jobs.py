from .client import ApiClient
from .requests import ShareResourceRequest


class ResourceSharing(ApiClient):
    def share(self, path: str, action: str, whom: str) -> bool:
        permissions = [{"uri": path, "action": action}]
        self._fetch_sync(ShareResourceRequest(whom, permissions))
        return True
