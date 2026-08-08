"""
Dynamic ORM Environment and ModelProxy implementation.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from .client import JSON2Client


class ModelProxy:
    """
    Dynamic proxy for an Odoo ORM model, providing an odoorpc-style interface over JSON-2 API.
    """

    def __init__(self, client: "JSON2Client", model_name: str):
        self._client = client
        self._model_name = model_name

    def __getattr__(self, method_name: str):
        """Dynamically dispatch method calls to client.call(model, method, ...)."""
        def method(*args, **kwargs):
            if args:
                if len(args) == 1 and isinstance(args[0], list) and method_name in ("read", "write", "unlink"):
                    kwargs["ids"] = args[0]
                elif len(args) == 2 and method_name == "write":
                    kwargs["ids"] = args[0]
                    kwargs["vals"] = args[1]
                elif len(args) == 1 and method_name == "create":
                    kwargs["vals_list"] = args[0] if isinstance(args[0], list) else [args[0]]
                elif len(args) == 1 and method_name == "search":
                    kwargs["domain"] = args[0]

            return self._client.call(self._model_name, method_name, **kwargs)

        return method

    def search(
        self,
        domain: List[Any],
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[int]:
        kwargs: Dict[str, Any] = {"domain": domain, "offset": offset}
        if limit is not None:
            kwargs["limit"] = limit
        if order is not None:
            kwargs["order"] = order
        return self._client.call(self._model_name, "search", **kwargs)

    def read(self, ids: List[int], fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {"ids": ids}
        if fields:
            kwargs["fields"] = fields
        return self._client.call(self._model_name, "read", **kwargs)

    def search_read(
        self,
        domain: List[Any],
        fields: Optional[List[str]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {"domain": domain, "offset": offset}
        if fields:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if order is not None:
            kwargs["order"] = order
        return self._client.call(self._model_name, "search_read", **kwargs)

    def search_count(self, domain: List[Any]) -> int:
        return self._client.call(self._model_name, "search_count", domain=domain)

    def fields_get(self, allfields: Optional[List[str]] = None, attributes: Optional[List[str]] = None) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {}
        if allfields:
            kwargs["allfields"] = allfields
        if attributes:
            kwargs["attributes"] = attributes
        return self._client.call(self._model_name, "fields_get", **kwargs)

    def create(self, vals_list: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[int]:
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        return self._client.call(self._model_name, "create", vals_list=vals_list)

    def write(self, ids: List[int], vals: Dict[str, Any]) -> bool:
        return self._client.call(self._model_name, "write", ids=ids, vals=vals)

    def unlink(self, ids: List[int]) -> bool:
        return self._client.call(self._model_name, "unlink", ids=ids)

    def __repr__(self) -> str:
        return f"<ModelProxy '{self._model_name}'>"


class Environment:
    """
    Environment dictionary accessor mimicking odoorpc.ODOO.env['model_name'].
    """

    def __init__(self, client: "JSON2Client"):
        self._client = client
        self._cache: Dict[str, ModelProxy] = {}

    def __getitem__(self, model_name: str) -> ModelProxy:
        if model_name not in self._cache:
            self._cache[model_name] = ModelProxy(self._client, model_name)
        return self._cache[model_name]

    def __contains__(self, model_name: str) -> bool:
        return True

    def __repr__(self) -> str:
        return f"<Environment client={self._client.host}>"
