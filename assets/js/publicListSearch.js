import Cookies from 'js-cookie';
import ReactDOM from "react-dom";
import React from 'react';
import ListSearch from './component/listSearch';
import Cleave from 'cleave.js/react';

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
    <form action="" method="post" autoComplete="off">
      <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')} />
      <ListSearch onChange={(person) => this.personChange(person)} />

      {ELECTRONIC_VOTE_REQUIRE_BIRTHDATE ?
        <div>
          <label>Date de naissance</label>
          <Cleave placeholder="jj/mm/aaaa"
                  className="form-control"
                options={{date: true, datePattern: ['d', 'm', 'Y']}}
                name="birth_date" />
        </div>
        : ''
      }
      <div className="input-group margintopless">
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
