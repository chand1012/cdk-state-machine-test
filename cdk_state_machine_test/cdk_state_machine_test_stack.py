import os

from aws_cdk import core as cdk
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks

from aws_cdk.aws_lambda_python import PythonFunction 

class CdkStateMachineTestStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        submit_lambda = PythonFunction(self, 'Submit',
            handler='handler',
            index='submit.py',
            entry=os.path.join(os.getcwd(), 'lambdas'),
            runtime=lambda_.Runtime.PYTHON_3_8
        )

        get_status_lambda = PythonFunction(self, 'Status',
            handler='handler',
            index='status.py',
            entry=os.path.join(os.getcwd(), 'lambdas'),
            runtime=lambda_.Runtime.PYTHON_3_8
        )

        submit_job = tasks.LambdaInvoke(self, "Submit Job",
            lambda_function=submit_lambda,
            # Lambda's result is in the attribute `Payload`
            output_path="$.Payload"
        )

        wait_x = sfn.Wait(self, "Wait X Seconds",
            time=sfn.WaitTime.seconds_path("$.waitSeconds")
        )

        get_status = tasks.LambdaInvoke(self, "Get Job Status",
            lambda_function=get_status_lambda,
            # Pass just the field named "guid" into the Lambda, put the
            # Lambda's result in a field called "status" in the response
            output_path="$.Payload"
        )

        job_failed = sfn.Fail(self, "Job Failed",
            cause="AWS Batch Job Failed",
            error="DescribeJob returned FAILED"
        )

        final_status = tasks.LambdaInvoke(self, "Get Final Job Status",
            lambda_function=get_status_lambda,
            # Use "guid" field as input
            output_path="$.Payload"
        )

        definition = submit_job.next(wait_x).next(get_status).next(sfn.Choice(self, "Job Complete?").when(sfn.Condition.string_equals("$.status", "FAILED"), job_failed).when(sfn.Condition.string_equals("$.status", "SUCCEEDED"), final_status).otherwise(wait_x))

        sfn.StateMachine(self, "StateMachine",
            definition=definition,
            timeout=cdk.Duration.minutes(5)
        )
