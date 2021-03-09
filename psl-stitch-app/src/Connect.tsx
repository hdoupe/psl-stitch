import React, { useCallback, useEffect } from "react";
import axios from "axios";
import { Container, Jumbotron } from "react-bootstrap";

import client from "./ApiClient";

export const ConnectComponent: React.FC<{}> = () => {
  const [config, setConfig] = React.useState<{
    authorization_uri: string;
    state: string;
  }>();

  const fetchConnect = useCallback(async () => {
    try {
      const resp = await client.get("/connect/");
      const data = resp.data;
      console.log("got data", data);
      setConfig(data);
    } catch (error) {
      console.log(error);
    }
  }, []);

  useEffect(() => {
    fetchConnect();
  }, [fetchConnect]);

  if (!config) {
    return <div />;
  }
  return (
    <Jumbotron className="vertical-center">
      <Container>
        <a href={config.authorization_uri}>
          Click this link to connect to Compute Studio
        </a>
      </Container>
    </Jumbotron>
  );
};
