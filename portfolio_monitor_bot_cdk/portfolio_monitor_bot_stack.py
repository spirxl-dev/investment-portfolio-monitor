from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct


class PortfolioMonitorBotStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        portfolio_monitor_function = lambda_.Function(
            self,
            "PortfolioMonitorFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(15),
        )

        rule = events.Rule(
            self,
            "DailyRule",
            schedule=events.Schedule.cron(minute="0", hour="6"),
        )

        rule.add_target(targets.LambdaFunction(portfolio_monitor_function))
