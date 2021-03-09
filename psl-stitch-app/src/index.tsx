import ReactDOM from "react-dom";
import "./index.css";
import { ConnectComponent } from "./Connect";
import { Stitch } from "./Stitch";
import { BrowserRouter, Route, Switch } from "react-router-dom";

console.log("api", process.env.REACT_APP_API_URL);

ReactDOM.render(
  <BrowserRouter>
    <Switch>
      <Route exact path="/connect/" render={() => <ConnectComponent />} />
    </Switch>
    <Switch>
      <Route exact path="/" render={() => <Stitch />} />
    </Switch>
  </BrowserRouter>,
  document.getElementById("root")
);
