"""
Bittensor service for the TAO Dividend Sentiment Service.

This module provides functionality for interacting with the Bittensor network,
including retrieving network information, hotkeys, and dividend data.
"""

from typing import List

from bittensor.core.async_subtensor import AsyncSubtensor
from bittensor.core.metagraph import Metagraph
from bittensor_wallet.wallet import Wallet


class BitTensorService(AsyncSubtensor):
    """
    Service for interacting with the Bittensor network.
    
    This class extends AsyncSubtensor to provide methods for retrieving
    network information, hotkeys, and dividend data from the Bittensor network.
    
    Attributes:
        netuid (int): Network UID for the service
        wallet_hotkey (str): Hotkey for the wallet
        wallet_name (str): Name of the wallet
        wallet (Wallet): Bittensor wallet instance
        meta_graph (Metagraph): Metagraph for the network
        bittensor (AsyncSubtensor): AsyncSubtensor instance
    """
    def __init__(self, netuid: int, wallet_hotkey: str, wallet_name: str) -> None:
        """
        Initialize the Bittensor service.
        
        Args:
            netuid (int): Network UID for the service
            wallet_hotkey (str): Hotkey for the wallet
            wallet_name (str): Name of the wallet
        """
        super().__init__()
        self.netuid: int = netuid
        self.wallet_hotkey: str = wallet_hotkey
        self.wallet_name: str = wallet_name
        self.wallet = Wallet(name=self.wallet_name, hotkey=self.wallet_hotkey)
        self.meta_graph: Metagraph = Metagraph(netuid=self.netuid)
        self.bittensor: AsyncSubtensor = AsyncSubtensor()

    async def get_all_netuids(self) -> List[int]:
        """
        Get all network UIDs from the Bittensor network.
        
        Returns:
            List[int]: List of all network UIDs
        """
        all_subnets = await self.bittensor.get_all_subnets_info()
        return [s.netuid for s in all_subnets]

    def get_hotkeys_for_netuid(self, netuid: int) -> List[str]:
        """
        Get all hotkeys for a specific network UID.
        
        Args:
            netuid (int): Network UID to query
            
        Returns:
            List[str]: List of hotkeys for the specified network UID
        """
        if netuid != self.netuid:
            return Metagraph(netuid=netuid).hotkeys
        return self.meta_graph.hotkeys

    def get_dividends_for_all_hot_keys(self, netuid: int) -> List[tuple]:
        """
        Get dividend information for all hotkeys in a specific network UID.
        
        Args:
            netuid (int): Network UID to query
            
        Returns:
            List[tuple]: List of tuples containing dividend information for each hotkey
        """
        if netuid != self.netuid:
            return Metagraph(netuid=netuid).tao_dividends_per_hotkey
        return self.meta_graph.tao_dividends_per_hotkey
