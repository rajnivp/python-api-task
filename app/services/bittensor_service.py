from typing import List, Dict, Any

from bittensor.core.async_subtensor import AsyncSubtensor
from bittensor.core.metagraph import Metagraph
from bittensor_cli.cli import Balance
from bittensor_wallet.wallet import Wallet


class BitTensorService(AsyncSubtensor):
    def __init__(self, netuid: int, wallet_hotkey: str, wallet_name: str) -> None:
        super().__init__()
        self.netuid: int = netuid
        self.wallet_hotkey: str = wallet_hotkey
        self.wallet_name: str = wallet_name
        self.wallet = Wallet(name=self.wallet_name, hotkey=self.wallet_hotkey)
        self.meta_graph: Metagraph = Metagraph(netuid=self.netuid)
        self.bittensor: AsyncSubtensor = AsyncSubtensor()

    async def get_all_netuids(self) -> List[int]:
        all_subnets = await self.bittensor.get_all_subnets_info()
        return [s.netuid for s in all_subnets]

    def get_hotkeys_for_netuid(self, netuid: int) -> List[str]:
        if netuid != self.netuid:
            return Metagraph(netuid=netuid).hotkeys
        return self.meta_graph.hotkeys

    def get_dividends_for_all_hot_keys(self, netuid: int) -> List[tuple]:
        if netuid != self.netuid:
            return Metagraph(netuid=netuid).tao_dividends_per_hotkey
        return self.meta_graph.tao_dividends_per_hotkey
