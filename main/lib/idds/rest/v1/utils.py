#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0OA
#
# Authors:
# - Wen Guan, <wen.guan@cern.ch>, 2020

from idds.common.constants import RequestType, RequestStatus

from idds.workflow.workflow import Workflow

# from idds.atlas.workflow.atlasstageinwork import ATLASStageInWork
# from idds.atlas.workflow.atlashpowork import ATLASHPOWork


def convert_stagein_request_metadata_to_workflow(scope, name, workload_id, request_metadata):
    """
    Convert old format stagein request metadata of json to new format request metadata based on workflow.

    :param scope: The collection scope.
    :param name: The collection name.
    :param workload_id: The workload id.
    :param request_metadata: The request metadata.
    """
    # 'request_metadata': {'workload_id': '20776840', 'max_waiting_time': 3600, 'src_rse': 'NDGF-T1_DATATAPE', 'dest_rse': 'NDGF-T1_DATADISK', 'rule_id': '236e4bf87e11490291e3259b14724e30'}  # noqa: E501

    from idds.atlas.workflow.atlasstageinwork import ATLASStageinWork

    work = ATLASStageinWork(executable=None, arguments=None, parameters=None, setup=None,
                            exec_type='local', sandbox=None,
                            primary_input_collection={'scope': scope, 'name': name},
                            other_input_collections=None,
                            output_collections={'scope': scope, 'name': name + '.idds.stagein'},
                            log_collections=None,
                            logger=None,
                            max_waiting_time=request_metadata.get('max_waiting_time', 3600 * 7 * 24),
                            src_rse=request_metadata.get('src_rse', None),
                            dest_rse=request_metadata.get('dest_rse', None),
                            rule_id=request_metadata.get('rule_id', None))
    wf = Workflow()
    wf.set_workload_id(workload_id)
    wf.add_work(work)
    # work.set_workflow(wf)
    return wf


def convert_hpo_request_metadata_to_workflow(scope, name, workload_id, request_metadata):
    """
    Convert old format hpo request metadata of json to new format request metadata based on workflow.

    :param scope: The collection scope.
    :param name: The collection name.
    :param workload_id: The workload id.
    :param request_metadata: The request metadata.
    """
    # 'request_metadata': {'workload_id': '20525134', 'sandbox': None, 'method': 'bayesian', 'opt_space': {'A': (1, 4), 'B': (1, 10)}, 'initial_points': [({'A': 1, 'B': 2}, 0.3), ({'A': 1, 'B': 3}, None)], 'max_points': 20, 'num_points_per_generation': 10}  # noqa: E501
    # 'request_metadata': {'workload_id': '20525135', 'sandbox': None, 'method': 'nevergrad', 'opt_space': {"A": {"type": "Choice", "params": {"choices": [1, 4]}}, "B": {"type": "Scalar", "bounds": [0, 5]}}, 'initial_points': [({'A': 1, 'B': 2}, 0.3), ({'A': 1, 'B': 3}, None)], 'max_points': 20, 'num_points_per_generation': 10}  # noqa: E501
    # 'request_metadata': {'workload_id': '20525134', 'sandbox': 'wguanicedew/idds_hpo_nevergrad', 'workdir': '/data', 'executable': 'docker', 'arguments': 'python /opt/hyperparameteropt_nevergrad.py --max_points=%MAX_POINTS --num_points=%NUM_POINTS --input=/data/%IN --output=/data/%OUT', 'output_json': 'output.json', 'opt_space': {"A": {"type": "Choice", "params": {"choices": [1, 4]}}, "B": {"type": "Scalar", "bounds": [0, 5]}}, 'initial_points': [({'A': 1, 'B': 2}, 0.3), ({'A': 1, 'B': 3}, None)], 'max_points': 20, 'num_points_per_generation': 10}  # noqa: E501

    from idds.atlas.workflow.atlashpowork import ATLASHPOWork

    work = ATLASHPOWork(executable=request_metadata.get('executable', None),
                        arguments=request_metadata.get('arguments', None),
                        parameters=request_metadata.get('parameters', None),
                        setup=None, exec_type='local',
                        sandbox=request_metadata.get('sandbox', None),
                        method=request_metadata.get('method', None),
                        container_workdir=request_metadata.get('workdir', None),
                        output_json=request_metadata.get('output_json', None),
                        opt_space=request_metadata.get('opt_space', None),
                        initial_points=request_metadata.get('initial_points', None),
                        max_points=request_metadata.get('max_points', None),
                        num_points_per_iteration=request_metadata.get('num_points_per_iteration', 10))
    wf = Workflow()
    wf.set_workload_id(workload_id)
    wf.add_work(work)
    return wf


def convert_old_req_2_workflow_req(data):
    if not data:
        return data

    if data['request_type'] == RequestType.Workflow:
        return data

    workload_id = None
    if 'workload_id' in data and data['workload_id']:
        workload_id = data['workload_id']
    elif 'workload_id' in data['request_metadata'] and data['request_metadata']['workload_id']:
        workload_id = data['request_metadata']['workload_id']

    if data['request_type'] in [RequestType.StageIn, RequestType.StageIn.value]:
        wf = convert_stagein_request_metadata_to_workflow(data['scope'], data['name'], workload_id,
                                                          data['request_metadata'])
        data['request_type'] = RequestType.Workflow
        data['transform_tag'] = 'workflow'
        data['status'] = RequestStatus.New
        data['workload_id'] = wf.get_workload_id()
        data['request_metadata'] = {'workload_id': wf.get_workload_id(),
                                    'workflow': wf}
        return data
    if data['request_type'] in [RequestType.HyperParameterOpt, RequestType.HyperParameterOpt.value]:
        wf = convert_hpo_request_metadata_to_workflow(data['scope'] if 'scope' in data else None,
                                                      data['name'] if 'name' in data else None,
                                                      workload_id,
                                                      data['request_metadata'])
        primary_init_work = wf.get_primary_initial_collection()
        if primary_init_work:
            data['scope'] = primary_init_work['scope']
            data['name'] = primary_init_work['name']

        data['request_type'] = RequestType.Workflow
        data['transform_tag'] = 'workflow'
        data['status'] = RequestStatus.New
        data['workload_id'] = wf.get_workload_id()
        data['request_metadata'] = {'workload_id': wf.get_workload_id(),
                                    'workflow': wf}
        return data
    return data
