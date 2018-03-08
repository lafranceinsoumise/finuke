import axios from '../lib/axios';
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
    this.opMode = this.props.mode === 'operator';

    this.labels = {
      departementHelp: this.opMode ? 'Département d\'inscription de la personne': 'Recherchez votre département ci-dessus.',
      communePlaceholder: 'Commune d\'inscription',
      communePromptText: 'Tapez le nom de la commune d\'inscription',
      personPlaceholder : 'Prénom NOM',
      personPromptText: this.opMode ? 'Prénom et nom de la personne': 'Tapez votre prénom et votre nom',
      noListHint: this.opMode ?
        'Vous devez faire voter la personne avec un bulletin orange.'
        : (<span>Vous pouvez voter en <a href="telephone">validant votre numéro de téléphone</a>.</span>)
    }
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
          { this.state.departementInfo ? this.state.departementInfo.name : this.labels.departementHelp }
        </p>
        {this.state.departementInfo && this.state.departementInfo.details == 'D' ?
          <div className="alert alert-warning">
            Nous ne disposons malheureusement pas du détail par communes des listes électorales de ce département.
            Effectuez une recherche sur tout le département.
          </div>
          : <div className="form-group">
            <Select
              value={this.state.commune}
              onChange={this.communeChange}
              options={this.communesChoice}
              disabled={!this.state.communesLoaded}
              placeholder={this.labels.communePlaceholder}
              searchPromptText={this.labels.communePromptText}/>
          </div>
        }
        <div className="form-group">
          <Async
            name="person"
            autoload={false}
            value={this.state.person}
            disabled={!this.state.departementInfo || !this.state.departementInfo.details || (this.state.departementInfo.details == 'C' && !this.state.commune)}
            onChange={this.personChange}
            loadOptions={this.searchPeople}
            placeholder={this.labels.personPlaceholder}
            searchPromptText={this.labels.personPromptText}
            loadingPlaceholder="Chargement..." />
        </div>
        { this.state.departementInfo && !this.state.departementInfo.details ?
          <div className="alert alert-warning">
            Nous ne disposons malheureusement pas des listes électorales de ce département.
            {this.labels.noListHint}
          </div>
        : '' }
      </div>
    );
  }
}

export default ListSearch;
