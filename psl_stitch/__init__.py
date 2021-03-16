import json

import cs_kit
import paramtools as pt
import taxcalc

name_mappings = {
    "PSLmodels/Cost-of-Capital-Calculator": {
        "policy": "Individual and Payroll Tax Parameters",
        "ccc": "Business Tax Parameters",
    },
    "PSLmodels/Tax-Cruncher": {"policy": "Policy", "taxcrunch": "Tax Information"},
    "PSLmodels/Tax-Brain": {"policy": "policy", "behavior": "behavior"},
}


def get_clients(bearer_token=None):
    kwargs = {}
    if bearer_token is not None:
        kwargs = {"token_type": "Bearer", "api_token": bearer_token}
    clients = {
        "PSLmodels/Tax-Brain": cs_kit.ComputeStudio("PSLmodels", "Tax-Brain", **kwargs),
        "PSLmodels/Tax-Cruncher": cs_kit.ComputeStudio(
            "PSLmodels", "Tax-Cruncher", **kwargs
        ),
        "PSLmodels/Cost-of-Capital-Calculator": cs_kit.ComputeStudio(
            "PSLmodels", "Cost-of-Capital-Calculator", **kwargs
        ),
    }
    if bearer_token is not None:
        for client in clients.values():
            client.auth_header = {"Authorization": f"Bearer {bearer_token}"}
    return clients


class InvalidJSON(Exception):
    def __init__(self, app, msg):
        self.app = app
        self.msg = msg
        super().__init__(msg)


async def create(
    policy_params=None,
    taxcrunch_params=None,
    ccc_params=None,
    behavior_params=None,
    bearer_token=None,
):
    stitch_params = {}
    for label, params in [
        ("policy", policy_params),
        ("taxcrunch", taxcrunch_params),
        ("ccc", ccc_params),
        ("behavior", behavior_params),
    ]:
        if params is None or not params:
            stitch_params[label] = {}
        else:
            try:
                read_params = pt.read_json(params)
                if label == "policy" and not taxcalc.is_paramtools_format(read_params):
                    pol = taxcalc.Policy()
                    pt_adj = pol.implement_reform(read_params)
                    stitch_params[label] = pol._validator_schema.dump(pt_adj)
                else:
                    stitch_params[label] = read_params
            except (
                ValueError,
                pt.ValidationError,
                json.JSONDecodeError,
                FileNotFoundError,
            ) as e:
                raise InvalidJSON(label, str(e))

    clients = get_clients(bearer_token=bearer_token)

    meta_parameters = {"year": 2021}

    responses = {}
    exceptions = {}
    for app, mappings in name_mappings.items():
        adjustment = {}
        for key, label in mappings.items():
            adjustment[label] = stitch_params[key]

        client = clients[app]
        print("creating simulation for ", app)
        try:
            response = await client.create(
                adjustment=adjustment,
                meta_parameters=meta_parameters,
                check_is_valid=False,
            )
            print("\tsuccessfully created simulation for", response["model_pk"])
            responses[app] = {
                "client": client,
                "detail": response,
                "model_pk": response["model_pk"],
                "ready": False,
            }
            client.update(
                model_pk=response["model_pk"],
                title="Created as a stitch",
                is_public=True,
            )
        except cs_kit.APIException as e:
            print("\terror creating simulation!")
            exceptions[app] = e
    return responses, exceptions


async def get_inputs(app, model_pk, bearer_token=None):
    client = get_clients(bearer_token=bearer_token)[app]
    status, data = await client.get_inputs_status(model_pk)
    return {"status": status, "detail": data}


async def get_sim(app, model_pk, bearer_token=None):
    client = get_clients(bearer_token=bearer_token)[app]
    return await client.detail(model_pk, wait=False, include_outputs=False)


def update_ready(responses):
    for response in responses.values():
        ready_resp = response["client"].detail(
            response["model_pk"], wait=False, include_outputs=False
        )
        response["status"] = ready_resp["status"]
        response["ready"] = ready_resp["status"] == "SUCCESS"


def is_ready(responses):
    ready = {}
    for app, data in responses.items():
        ready[app] = data["ready"]
    return ready


def update_results(responses):
    for response in responses:
        detail_resp = response["client"].detail(
            response["model_pk"], wait=False, include_outputs=True
        )
        response["status"] = detail_resp["status"]
        if response["status"] == "SUCCESS":
            response["outputs"] = detail_resp["outputs"]
