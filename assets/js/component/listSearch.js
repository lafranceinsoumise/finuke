import axios from 'axios';
import React from 'react';
import Select from 'react-select';
import {Async} from 'react-select';
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

class ListSearch extends React.Component {
  constructor(props) {
    super(props);
    this.state = {departement: '', commune: null, communesLoaded: false, person: null};
    this.departementChange = this.departementChange.bind(this);
    this.communeChange = this.communeChange.bind(this);
    this.searchPeople = this.searchPeople.bind(this);
    this.personChange = this.personChange.bind(this);
  }

  async departementChange(event) {
    if (isNaN(event.target.value)) {
      return;
    }

    let departementInfo = findDepartement(event.target.value);

    this.setState({
      departement: event.target.value,
      departementInfo : departementInfo,
      commune: null,
      communesLoaded: false,
    });

    if (!departementInfo || departementInfo.details !== 'C') {
      return;
    }

    this.communesChoice = (await axios('/json/communes/' + event.target.value)).data.map(c => ({value: c.code, label: c.name}));

    this.setState({communesLoaded: true});
  }

  communeChange(commune) {
    this.setState({commune});
  }

  async searchPeople(input) {
    if (input.length < 4) return [];

    let qs = this.state.commune ? `?commune=${this.state.commune.value}` : '';

    let options = (await axios(`/json/listes/${this.state.departementInfo.code}/${input}${qs}`)).data
      .map(p => ({value: p.id, label: `${p.first_names} ${p.last_name} - ${p.commune_name}`}));

    return {options};
  }

  personChange(person) {
    this.setState({person});
    if (this.props.onChange) {
      this.props.onChange(person);
    }
  }

  render() {
    return (
      <div>
        <div className="form-group">
          <input placeholder="Numéro de département" type="text" className="text-center form-control input-lg" value={this.state.departement} onChange={this.departementChange} />
        </div>
        <p className="text-center">
          { this.state.departementInfo ? this.state.departementInfo.name : 'Recherchez votre département ci-dessus.' }
        </p>
        <div className="form-group">
          <Select
            value={this.state.commune}
            onChange={this.communeChange}
            options={this.communesChoice}
            disabled={!this.state.communesLoaded}
            placeholder="Commune d'inscription"
            searchPromptText="Tapez le nom de votre commune d'inscription" />
        </div>
        <div className="form-group">
          <Async
            name="person"
            autoload={false}
            value={this.state.person}
            disabled={!this.state.departementInfo || (this.state.communesLoaded && !this.state.commune)}
            onChange={this.personChange}
            loadOptions={this.searchPeople}
            placeholder="Recherchez vous sur les listes"
            searchPromptText="Tapez votre nom et prénom"
            loadingPlaceholder="Chargement..." />
        </div>
      </div>
    );
  }
}

export default ListSearch;