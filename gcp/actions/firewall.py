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

### Firewall rules

def gcp_create_firewall_rule(
        project_id: str,direction: str,source_ranges: list ,firewall_rule_name: str, network: str = "global/networks/default"
) -> compute_v1.Firewall:
    """
    Creates a simple firewall rule allowing for incoming HTTP and HTTPS access from the entire Internet.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
        firewall_rule_name: name of the rule that is created.
        network: name of the network the rule will be applied to. Available name formats:
            * https://www.googleapis.com/compute/v1/projects/{project_id}/global/networks/{network}
            * projects/{project_id}/global/networks/{network}
            * global/networks/{network}
        direction: INGRESS / EGRESS
        source_ranges: cidr address

    Returns:
        A Firewall object.
    """
    firewall_rule = compute_v1.Firewall()
    firewall_rule.name = firewall_rule_name
    # firewall_rule.direction = "INGRESS"
    firewall_rule.direction = direction

    allowed_ports = compute_v1.Allowed()
    allowed_ports.I_p_protocol = "tcp"
    allowed_ports.ports = ["80", "443"]

    firewall_rule.allowed = [allowed_ports]
    # firewall_rule.source_ranges = ["0.0.0.0/0"]
    firewall_rule.source_ranges = source_ranges
    firewall_rule.network = network
    firewall_rule.description = "Allowing TCP traffic on port 80 and 443 from Internet."

    firewall_rule.target_tags = ["web"]

    # Note that the default value of priority for the firewall API is 1000.
    # If you check the value of `firewall_rule.priority` at this point it
    # will be equal to 0, however it is not treated as "set" by the library and thus
    # the default will be applied to the new rule. If you want to create a rule that
    # has priority == 0, you need to explicitly set it so:
    # TODO: Uncomment to set the priority to 0
    # firewall_rule.priority = 0

    firewall_client = compute_v1.FirewallsClient()
    operation = firewall_client.insert(
        project=project_id, firewall_resource=firewall_rule
    )

    wait_for_extended_operation(operation, "firewall rule creation")

    return firewall_client.get(project=project_id, firewall=firewall_rule_name)

def gcp_delete_firewall_rule(project_id: str, firewall_rule_name: str) :
    """
    Deletes a firewall rule from the project.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
        firewall_rule_name: name of the firewall rule you want to delete.
    """
    firewall_client = compute_v1.FirewallsClient()
    operation = firewall_client.delete(project=project_id, firewall=firewall_rule_name)

    return wait_for_extended_operation(operation, "firewall rule deletion")

def gcp_list_firewall_rules(project_id: str) -> Iterable[compute_v1.Firewall]:
    """
    Return a list of all the firewall rules names in specified project.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.

    Returns:
        A flat list of all firewall rules names for given project.
    """
    firewall_client = compute_v1.FirewallsClient()
    firewalls_list = firewall_client.list(project=project_id)

    #Simple --> return just firewall rule name
    # return [fw.name for fw in firewalls_list]

    firewalls_details_l = []

    for fw in firewalls_list:
        firewalls_details_l.append({"name":fw.name,
                                    "description":fw.description,
                                    "id":fw.id,
                                    "direction":fw.direction,
                                    "network":fw.network})

    return firewalls_details_l


class FireWallRuleListRequest(BaseModel):
    project_id: str = "test"

@action_store.kubiya_action()
def get_firewall_rules(rule: FireWallRuleListRequest):
    try:
        results = gcp_list_firewall_rules(project_id=rule.project_id)
        return {"success": True, "results":results }
    except Exception as e:
        raise e


class FirewallRuleCreationRequest(BaseModel):
    firewall_rule_name: str = "test"
    project_id: str = "test"
    direction: str = "INGRESS"
    source_ranges: list=["0.0.0.0/0"]

@action_store.kubiya_action()
def create_firewall_rule(rule: FirewallRuleCreationRequest):
    try:
        results = gcp_create_firewall_rule(project_id=rule.project_id, firewall_rule_name=rule.firewall_rule_name, direction=rule.direction,source_ranges=rule.source_ranges)
        return {"success": True, "results":{"id":results.id,"name":results.name,"source_ranges":results.source_ranges} }
    except Exception as e:
        raise e

class FirewallRuleDeletionRequest(BaseModel):
    rule_name: str = "test"
    project_id: str = "test"

@action_store.kubiya_action()
def delete_firewall_rule(rule: FirewallRuleDeletionRequest):
    try:
        results=gcp_delete_firewall_rule(project_id=rule.project_id, firewall_rule_name=rule.rule_name)
        return {"success": True, "results":results }
    except Exception as e:
        raise e