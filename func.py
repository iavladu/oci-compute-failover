#
# oci_compute_failover version 1.0.
#
# Created by: ionut.vladu@oracle.com
#

import io
import json
import oci

from fdk import response

def instance_status(compute_client, instance_id):
    return compute_client.get_instance(instance_id).data.lifecycle_state

def instance_start(compute_client, instance_id):
    print('Starting Instance: {}'.format(instance_id))
    try:
        if instance_status(compute_client, instance_id) in 'STOPPED':
            try:
                resp = compute_client.instance_action(instance_id, 'START')
                print('Start response code: {0}'.format(resp.status))
            except oci.exceptions.ServiceError as e:
                print('Starting instance failed. {0}' .format(e))
                raise
        else:
            print('The instance was not STOPPED, so cannot be STARTED ' .format(instance_id))
    except oci.exceptions.ServiceError as e:
        print('Starting instance failed. {0}'.format(e))
        raise
    print('Started Instance: {}'.format(instance_id))
    return instance_status(compute_client, instance_id)

def instance_stop(compute_client, instance_id):
    print('Stopping Instance: {}'.format(instance_id))
    try:
        if instance_status(compute_client, instance_id) in 'RUNNING':
            try:
                resp = compute_client.instance_action(instance_id, 'STOP')
                print('Stop response code: {0}'.format(resp.status))
            except oci.exceptions.ServiceError as e:
                print('Stopping instance failed. {0}' .format(e))
        else:
            print('The instance was not RUNNING, so cannot be STOPPED ' .format(instance_id))
    except oci.exceptions.ServiceError as e:
        print('Stopping instance failed. {0}'.format(e))
    print('Stopped Instance: {}'.format(instance_id))

def handler(ctx, data: io.BytesIO=None):
    try:
        body = json.loads(data.getvalue())
        # get the state of the alarm
        alarm_status = body.get("alarmMetaData")[0]["status"]
        
        # get the OCID for the two VMs from the Configuration Variables
        cfg = ctx.Config()
        primary_vm_ocid = cfg["primary_vm"]
        failover_vm_ocid = cfg["failover_vm"]
        
        # the state must be FIRING in order to do the failover
        if alarm_status == "FIRING":
            try:
                print("Authenticate using Instance Principals")
                signer = oci.auth.signers.get_resource_principals_signer()
                compute_client = oci.core.ComputeClient(config={}, signer=signer)
            except (Exception) as ex:
                print("Could not authenticate using instance principals. Please check policies,")
                print(str(ex), flush=True)
                raise
                
            print("Stopping primary instance...")
            instance_stop(compute_client, primary_vm_ocid)
            
            print("Starting failover instance...")
            instance_start(compute_client, failover_vm_ocid)
            
        resp = "Failover process DONE successfully"
            
    except (Exception) as ex:
        print("Something went wrong with the call to the function")
        print(str(ex), flush=True)
        raise

    return response.Response(
        ctx, 
        response_data=json.dumps({"status": "{0}".format(resp)}),
        headers={"Content-Type": "application/json"}
    )