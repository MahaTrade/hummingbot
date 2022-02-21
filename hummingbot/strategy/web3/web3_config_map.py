from hummingbot.client.config.config_var import ConfigVar

# Returns a market prompt that incorporates the connector value set by the user


# List of parameters defined by the strategy
web3_config_map = {
    "strategy":
        ConfigVar(key="strategy",
                  prompt="",
                  default="web3",
                  ),
    "infura_url":
        ConfigVar(key="connector",
                  prompt="Enter Infura URL",
                  prompt_on_new=True,
                  ),
    "contract_address":
        ConfigVar(key="market",
                  prompt='Enter Contract address',
                  prompt_on_new=True,
                  )
}
