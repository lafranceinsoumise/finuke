import axios from 'axios';
import React from 'react';
import ReactDOM from 'react-dom';
import Select from 'react-select';
import 'react-select/dist/react-select.css';
import 'babel-polyfill';

import departementsData from 'CSVData/departements.csv';

const departements = departementsData.map(({
  CodeDept: code,
  NomDept,
  NomDeptEnr: name,
  TypNom,
  CodeRegion,
  ChefLieuDept,
  PopVotNuc,
  Intégration,
  PhyFile,
  NivDetail: details
}) => ({code, name, details}));

function findDepartement(number) {
  return departements.find(line => line.code == number);
}

class App extends React.Component {
  constructor() {
    super();
    this.state = {departement: '', commune: ''};
    this.departementChange = this.departementChange.bind(this);
    this.communeChange = this.communeChange.bind(this);
  }

  async departementChange(event) {
    if (isNaN(event.target.value)) {
      return;
    }

    let departementInfo = findDepartement(event.target.value);

    this.setState({
      departement: event.target.value,
      departementInfo : departementInfo,
      communesLoaded: false,
    });

    if (!departementInfo || departementInfo.details !== 'C') {
      return;
    }

    this.communesChoice = (await axios('/json/communes/' + event.target.value)).data.map(c => ({value: c.code, label: c.name}));

    this.setState({communesLoaded: true});
  }

  communeChange(commune) {
    this.setState({commune: commune.value});
  }

  render() {
    return (
      <div className="row">
        <div className="col-responsive">
          <p>
            <input placeholder="Numéro de département" type="text" className="text-center form-control input-lg" value={this.state.departement} onChange={this.departementChange} />
          </p>
          <p className="text-center">
            { this.state.departementInfo ? this.state.departementInfo.name : 'Recherchez votre département ci-dessus.' }
          </p>
          <p>
          {this.state.communesLoaded ?
          <Select
            value={this.state.commune}
            onChange={this.communeChange}
            options={this.communesChoice}
          /> : '' }
          </p>
          <input className="text-center form-control input-lg" placeholder="Prénoms et nom" />
        </div>
      </div>
    );
  }
}

ReactDOM.render(
  <App />,
  document.getElementById('react-root')
);