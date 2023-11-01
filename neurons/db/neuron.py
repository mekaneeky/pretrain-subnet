import bittensor as bt


class DB:

    def __init__( self, config ):

        # === Config ===
        self.config = config

        # === Logging ===
        bt.logging(config=config, logging_dir=config.full_path)
        bt.logging.info( f"Running miner for subnet: { pretrain.NETUID } on network: {config.subtensor.chain_endpoint} with config:")
        bt.logging.info(self.config)

        # === Bittensor objects ===
        self.wallet = bt.wallet( config = self.config ) 
        self.subtensor = bt.subtensor( config = self.config )
        self.metagraph = self.subtensor.metagraph( pretrain.NETUID )
        if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys: raise Exception("You are not registered. Use `btcli s recycle_register` to register.")
        self.uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        bt.logging.info(f"Wallet: {self.wallet}")
        bt.logging.info(f"Subtensor: {self.subtensor}")
        bt.logging.info(f"Metagraph: {self.metagraph}")
        bt.logging.info(f"Running miner on uid: {self.uid}")

        # === Init wandb ===
        self.wandb = init_wandb( self, type = 'miner', uid = self.uid )

        # === Locks ===
        # Limits GPU usage to 1 request at a time for space considerations. In practice, we would
        # shuttle multiple requests across multiple machines.
        self.gpu_lock = asyncio.Lock() 
        # Limits the number of queries that can pass the header checks in the blacklist.
        # Increasing this number allow for the miner to download more requests concurrently.
        self.global_forward_lock = asyncio.Semaphore( self.config.max_concurrent_forward_requests ) 

        # === Axon Callbacks ===
        async def priority_fn( synapse: pretrain.protocol.ComputeGradients ) -> float: return await priority( self, synapse )
        async def blacklist_fn( synapse: pretrain.protocol.ComputeGradients ) -> typing.Tuple[bool, str]: return await blacklist( self, synapse )
        async def compute_gradients_fn( synapse: pretrain.protocol.ComputeGradients ) -> pretrain.protocol.ComputeGradients: return await compute_gradients( self, synapse )

        # === Axon ===
        self.axon = bt.axon( 
            wallet = self.wallet, 
            config = self.config 
        ).attach( 
            forward_fn = compute_gradients_fn,
            priority_fn = priority_fn,
            blacklist_fn = blacklist_fn
        ).start()
        bt.logging.info(f"Served Axon {self.axon} on network: on network: {self.config.subtensor.chain_endpoint} with netuid: {pretrain.NETUID}")