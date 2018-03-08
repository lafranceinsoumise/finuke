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
    if (!this.state.person) {
      return <ListSearch mode="operator" onChange={(person) => this.personChange(person)} />;
    }

    return (
      <div>
        Voulez-vous vraiment faire voter {this.state.person.label}&nbsp;?
        <form action="" method="post">
          <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')} />
          <input type="hidden" name="person" value={this.state.person.value} />
          <input type="submit" className="btn btn-primary" value="Faire voter cette personne" />
        </form>
      </div>
    )
  }
}


ReactDOM.render(
  <App />,
  document.getElementById('react-root')
);
