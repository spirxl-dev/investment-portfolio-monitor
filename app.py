#!/usr/bin/env python3

import aws_cdk as cdk

from portfolio_monitor_bot_cdk.portfolio_monitor_bot_stack import (
    PortfolioMonitorBotStack,
)


app = cdk.App()
PortfolioMonitorBotStack(app, "PortfolioMonitorBotStack")

app.synth()
