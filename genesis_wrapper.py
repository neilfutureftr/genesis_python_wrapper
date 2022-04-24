import itertools
from pyserum.connection import conn
import requests
from solana.rpc.api import Client
from typing import Any, Optional, cast
from solana.rpc.providers.base import BaseProvider
from solana.rpc._utils.encoding import FriendlyJsonSerde
from solana.rpc.types import URI, RPCMethod, RPCResponse
import json
import time
import base64


#We have to change a bit the regular HTTP client of the solana library
class HTTPProvider(BaseProvider, FriendlyJsonSerde):
    """HTTP provider interact with the http rpc endpoint."""


    def __init__(self, endpoint = None,id_shdw=None,pass_shdw=None):
        """Init HTTPProvider."""
        self._request_counter = itertools.count()
        self.id_shdw=id_shdw
        self.passwd_shdw=pass_shdw
        self.ulr_update_token="https://auth.genesysgo.net/auth/realms/RPCs/protocol/openid-connect/token"
        self.token_time_to_refresh =0
        self.header_token=""
        self.refresh_token()
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)


    def refresh_token(self):
        token_avt = self.id_shdw + ":" + self.passwd_shdw
        token_avt = base64.b64encode(token_avt.encode('ascii'))
        r = requests.post(self.ulr_update_token, data={"grant_type": "client_credentials"}, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + str(token_avt)[2:-1]},
                          timeout=10)
        jjson = json.loads(r.content.decode('utf-8'))
        self.token_time_to_refresh=time.time()+jjson['expires_in']
        self.header_token=jjson["access_token"]

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"HTTP RPC connection {self.endpoint_uri}"

    def make_request(self, method: RPCMethod, *params) -> RPCResponse:
        """Make an HTTP request to an http rpc endpoint."""
        request_id = next(self._request_counter) + 1
        if self.token_time_to_refresh<time.time():
            self.refresh_token()
        if self.header_token==None:
            headers = {"Content-Type": "application/json"}
        else:
            headers = {"Content-Type": "application/json","Authorization": "Bearer " +self.header_token}
        data = self.json_encode({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        raw_response = requests.post(self.endpoint_uri, headers=headers, data=data)
        raw_response.raise_for_status()
        return cast(RPCResponse, self.json_decode(raw_response.text))

    def is_connected(self) -> bool:
        """Health check."""
        try:
            response = requests.get(f"{self.endpoint_uri}/health")
            response.raise_for_status()
        except (IOError, requests.HTTPError) as err:

            return False

        return response.ok




id_shdw = ""#Name of your SHDW client access (set up via discord)
passwd_shdw = ""#Name of your SHDW client access (set up via discord)
URL_RPC_access=""#URL of your SHDW RPC access


#We create the special HTTP connectoooor described above
http_locc=HTTPProvider(URL_RPC_access,id_shdw,passwd_shdw)
#We create a regular solana client
http_client = Client("https://api.mainnet-beta.solana.com")
#We change the http connector of the regular account with the custom made http connectooor
http_client._provider=http_locc
usdc_address="7kEHXrMauf9DhdTTueb4SB5R1eZWtMhm3gzDWTtbDjut" #Token account of USDC
print(http_client.get_token_account_balance(usdc_address)["result"]["value"]['uiAmount'])
