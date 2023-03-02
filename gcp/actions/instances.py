from . import action_store
import sys
from pydantic import BaseModel
from typing import Any
from google.api_core.extended_operation import ExtendedOperation
from typing import Iterable
from google.cloud import compute_v1

def wait_for_extended_operation(
        operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
) -> Any:
    """
    Waits for the extended (long-running) operation to complete.

    If the operation is successful, it will return its result.
    If the operation ends with an error, an exception will be raised.
    If there were any warnings during the execution of the operation
    they will be printed to sys.stderr.

    Args:
        operation: a long-running operation you want to wait on.
        verbose_name: (optional) a more verbose name of the operation,
            used only during error and warning reporting.
        timeout: how long (in seconds) to wait for operation to finish.
            If None, wait indefinitely.

    Returns:
        Whatever the operation.result() returns.

    Raises:
        This method will raise the exception received from `operation.exception()`
        or RuntimeError if there is no exception set, but there is an `error_code`
        set for the `operation`.

        In case of an operation taking longer than `timeout` seconds to complete,
        a `concurrent.futures.TimeoutError` will be raised.
    """
    result = operation.result(timeout=timeout)

    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True,
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

    return result

### GCP Instances

def gcp_reset_instance(project_id: str, zone: str, instance_name: str):
    """
    Resets a stopped Google Compute Engine instance (with unencrypted disks).
    Args:
        project_id: project ID or project number of the Cloud project your instance belongs to.
        zone: name of the zone your instance belongs to.
        instance_name: name of the instance your want to reset.
    """
    instance_client = compute_v1.InstancesClient()

    operation = instance_client.reset(
        project=project_id, zone=zone, instance=instance_name
    )

    return wait_for_extended_operation(operation, "instance reset")


def gcp_list_instances(project_id: str, zone: str) -> Iterable[compute_v1.Instance]:
    """
    List all instances in the given zone in the specified project.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
        zone: name of the zone you want to use. For example: “us-west3-b”
    Returns:
        An iterable collection of Instance objects.
    """
    instance_client = compute_v1.InstancesClient()
    instance_list = instance_client.list(project=project_id, zone=zone)


    instances_details_l = []

    for inst in instance_list:
        instances_details_l.append({"name":inst.name,
                                    "id":inst.id,
                                    "creation_date":inst.creation_timestamp,
                                    "machine_type":inst.machine_type,
                                    "status":inst.status,
                                    "zone":inst.zone
                                    })

    return instances_details_l



class InstancesListRequest(BaseModel):
    project_id: str = "test"
    zone:str = "test"

@action_store.kubiya_action()
def get_instances(inst: InstancesListRequest):
    try:
        results = gcp_list_instances(project_id=inst.project_id,zone=inst.zone)
        return {"success": True, "results":results }
    except Exception as e:
        raise e

class InstanceReset(BaseModel):
    project_id: str = "test"
    zone:str = "test"
    instance_name:str ="test"
@action_store.kubiya_action()
def reset_instance(inst: InstanceReset):

    try:
        results =gcp_reset_instance(project_id=inst.project_id,zone=inst.zone,instance_name=inst.instance_name)
        return {"success": True, "results":results }
    except Exception as e:
        raise e