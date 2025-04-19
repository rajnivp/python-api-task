import asyncio

from bittensor import AsyncSubtensor
from bittensor_cli.cli import Balance
from bittensor_wallet.wallet import Wallet
from mnemonic import Mnemonic


def generate_mnemonic_and_seed():
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.generate(strength=256)  # 24-word phrase
    seed = mnemo.to_seed(mnemonic_phrase).hex()

    return mnemonic_phrase, seed


w_name = "diamond like interest affair safe clarify lawsuit innocent beef van grief color"
h_key = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
bt = AsyncSubtensor()
# pprint.pprint(asyncio.run(bt.get_all_subnets_info()))
# exit()
wallet = Wallet(name=w_name,
                hotkey="5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v")
# # res = asyncio.run(wallet_balance(wallet=wallet, subtensor=bt, all_balances=True))
# res = asyncio.run(bt.get_all_metagraphs_info())
#
# print(res)
# exit()
# exit()

# res = asyncio.run(transfer(wallet=wallet, destination=h_key, subtensor=bt, amount=1000, era=1, transfer_all=True, prompt='', json_output=True))
# print(res)
# exit()

# phrase, seed = generate_mnemonic_and_seed()
# ck = wallet.regenerate_hotkey(mnemonic=phrase, seed=seed)
# print(ck)
balance = Balance.from_rao(amount=1000000)
print(balance)

res = asyncio.run(bt.add_stake(wallet=wallet, netuid=18, amount=balance, hotkey_ss58=h_key))
#
print(res)
exit()
