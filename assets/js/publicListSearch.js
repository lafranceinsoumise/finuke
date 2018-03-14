import Cookies from 'js-cookie';
import ReactDOM from "react-dom";
import React from 'react';
import ListSearch from './component/listSearch';

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  personChange(person) {
    this.setState({person});
  }

  render() {
    return (
    <form action="" method="post" autocomplete="off">
      <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')} />
      <ListSearch onChange={(person) => this.personChange(person)} />
      <div className="input-group">
        <label><input type="checkbox" required />
          &nbsp;J'atteste sur l'honneur de mon identité. Mon vote sera anonyme et confidentiel.</label>
      </div>
      <input type="submit" className="btn btn-primary" value="Je veux voter" disabled={!this.state.person} />
    </form>
    );
  }
}

ReactDOM.render(
  <App />,
  document.getElementById('react-root')
);
