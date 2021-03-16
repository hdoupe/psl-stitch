import React, { useCallback, useEffect, useState } from "react";
import { Col, Container, Row } from "react-bootstrap";
import { Formik, FormikProps, Form, Field } from "formik";

import client from "./ApiClient";

interface Me {
  username: string;
  status: string;
}

interface PSLStitch {
  policy_params: string;
  taxcrunch_params: string;
  ccc_params: string;
  behavior_params: string;
}

const initialValues: PSLStitch = {
  policy_params: "",
  taxcrunch_params: "",
  ccc_params: "",
  behavior_params: "",
};

interface AppException {
  owner: string;
  title: string;
  msg: string;
}

interface AppResponse {
  model_pk?: number;
  status: string;
  ready: boolean;
  project: string;
  url?: string;
  exception?: AppException;
}

const Input: React.FC<{ children: JSX.Element[] }> = ({ children }) => (
  <Row className="w-100 py-3">
    <Col className="col-auto">{children}</Col>
  </Row>
);

interface Inputs {
  model_pk: number;
  status: string;
  errors_warnings: any;
  traceback?: string;
  sim: Sim;
}

interface Sim {
  status: string;
  model_pk: number;
  eta: number;
  title: string;
  owner: string;
}

var inputsTimers: { [app: string]: NodeJS.Timeout } = {};

const pollInputs = (
  app: string,
  model_pk: number,
  inputs: Inputs | undefined,
  setInputs: (inputs: Inputs) => void
) => {
  inputsTimers[app] = setTimeout(async () => {
    if (!model_pk) return;
    if (
      inputs?.status &&
      (inputs?.status === "SUCCESS" || inputs?.status === "INVALID") &&
      inputs?.model_pk === model_pk
    )
      return clearTimeout(inputsTimers[app]);
    try {
      const resp = await client.get(`/inputs/${app}/${model_pk}/`);
      setInputs(resp.data.detail);
      inputs = resp.data.detail;
      if (inputs?.status !== "SUCCESS" && inputs?.status !== "INVALID") {
        inputsTimers[app] = pollInputs(app, model_pk, inputs, setInputs);
      } else {
        clearTimeout(inputsTimers[app]);
      }
    } catch (error) {
      if (error.response.status === 403) {
        window.location.href = "/connect/";
      }
    }
  }, 3000);
  return inputsTimers[app];
};

var simTimers: { [app: string]: NodeJS.Timeout } = {};

const pollSim = (
  app: string,
  model_pk: number,
  inputs: Inputs,
  sim: Sim | undefined,
  setSim: (sim: Sim) => void
): NodeJS.Timeout => {
  simTimers[app] = setTimeout(async () => {
    if (!model_pk) return;
    if (
      sim?.status &&
      (inputs?.status === "INVALID" ||
        sim?.status === "SUCCESS" ||
        sim?.status === "FAIL") &&
      inputs?.model_pk === model_pk &&
      sim?.model_pk === model_pk
    )
      return clearTimeout(simTimers[app]);
    try {
      const resp = await client.get(`/sim/${app}/${model_pk}/`);
      setSim(resp.data);
      sim = resp.data;
      if (sim?.status !== "SUCCESS" && sim?.status !== "FAIL") {
        simTimers[app] = pollSim(app, model_pk, inputs, sim, setSim);
      } else {
        return clearTimeout(simTimers[app]);
      }
    } catch (error) {
      if (error.response.status === 403) {
        window.location.href = "/connect/";
      }
    }
  }, 5000);
  return simTimers[app];
};

const SimComponent: React.FC<{
  app: string;
  model_pk?: number;
  url?: string;
}> = ({ app, model_pk, url }) => {
  const [inputs, setInputs] = useState<Inputs>();
  const [sim, setSim] = useState<Sim>();

  useEffect(() => {
    if (!model_pk) return;
    clearTimeout(inputsTimers[app]);
    pollInputs(app, model_pk, inputs, setInputs);
  }, [model_pk]);

  useEffect(() => {
    if (!model_pk || !inputs) return;
    if (inputs.status === "INVALID") {
      clearTimeout(simTimers[app]);
      return;
    }
    clearTimeout(simTimers[app]);
    pollSim(app, model_pk, inputs, sim, setSim);
  }, [model_pk, inputs?.status]);

  return (
    <Row className="py-2">
      <Col>
        <h4>{app}</h4>
        <h6>{!!sim && `${sim.title} by ${sim.owner}`}</h6>
        <p>{url && <a href={url}>ID: {model_pk}</a>}</p>
        <p>Inputs status: {inputs?.status || "STARTING"}</p>
        <p>Sim status: {sim?.status || "STARTING"}</p>
        {(inputs?.status === "INVALID" || inputs?.traceback) && (
          <pre>
            <code>
              {inputs?.traceback ||
                JSON.stringify(inputs.errors_warnings, null, 2)}
            </code>
          </pre>
        )}
        {sim?.status === "SUCCESS" && (
          <details>
            <summary>API Response for Simulation</summary>
            <pre>
              <code>{JSON.stringify(sim, null, 2)}</code>
            </pre>
          </details>
        )}
      </Col>
    </Row>
  );
};

export const Stitch: React.FC<{}> = () => {
  const [results, setResults] = React.useState<Array<AppResponse>>();

  const fetchConnect = useCallback(async () => {
    try {
      const resp = await client.get("/me/");
      const me: Me = resp.data;
      if (me.status === "anon") {
        window.location.href = "/connect/";
      }
    } catch (error) {
      console.log(error);
      if (error.response.status === 403) {
        window.location.href = "/connect/";
      }
    }
  }, []);

  useEffect(() => {
    fetchConnect();
  }, [fetchConnect]);

  return (
    <Container>
      <h1>PSL Stitch</h1>

      <Formik
        initialValues={initialValues}
        onSubmit={async (values, actions) => {
          console.log({ values, actions });
          try {
            const resp = await client.post("/create/", values);
            actions.setStatus({ invalid: null });
            setResults(resp.data as Array<AppResponse>);
          } catch (error) {
            actions.setStatus({
              invalid: JSON.stringify(error.response.data, null, 2),
            });
          }

          actions.setSubmitting(false);
        }}
      >
        {(props: FormikProps<PSLStitch>) => (
          <>
            {props.status && props.status.invalid && (
              <div>
                <pre>
                  <code>{props.status.invalid}</code>
                </pre>
              </div>
            )}
            <Form>
              <Input>
                <label className="pr-2" htmlFor="policy_params">
                  Policy Parameters
                </label>

                <Field
                  id="policy_params"
                  name="policy_params"
                  as="textarea"
                  placeholder="{}"
                />
              </Input>

              <Input>
                <label className="pr-2" htmlFor="taxcrunch_params">
                  Taxcrunch Parameters
                </label>

                <Field
                  id="taxcrunch_params"
                  name="taxcrunch_params"
                  placeholder="{}"
                  as="textarea"
                />
              </Input>

              <Input>
                <label className="pr-2" htmlFor="ccc_params">
                  CCC Parameters
                </label>

                <Field
                  id="ccc_params"
                  as="textarea"
                  name="ccc_params"
                  placeholder="{}"
                />
              </Input>

              <Input>
                <label className="pr-2" htmlFor="behavior_params">
                  Behavior Parameters
                </label>

                <Field
                  id="behavior_params"
                  name="behavior_params"
                  placeholder="{}"
                  as="textarea"
                />
              </Input>

              <button type="submit" className="btn btn-primary">
                Submit
              </button>
            </Form>

            {!!results && (
              <div className="mt-2">
                {results.map((value) => (
                  <SimComponent
                    key={value.project}
                    app={value.project}
                    model_pk={value.model_pk}
                    url={value.url}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </Formik>
    </Container>
  );
};
